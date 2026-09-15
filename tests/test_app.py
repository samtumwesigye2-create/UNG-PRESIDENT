import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ung_president as app
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client(tmp_path):
    app.DB_PATH = str(tmp_path / 'test.db')
    app.DATABASE_URL = ''
    app._rate_buckets.clear()
    with contextlib.redirect_stdout(io.StringIO()):
        with TestClient(app.app) as c:
            yield c


def test_password_policy():
    assert app.password_meets_policy('short')[0] is False
    assert app.password_meets_policy('Strong-password-123')[0] is True


def test_public_pages_and_admin_guard(client):
    for path in ['/', '/executive-orders', '/honours', '/visit', '/petition', '/admin/login', '/admin/register']:
        assert client.get(path).status_code == 200
    assert client.get('/admin/executive-orders').status_code == 401


def test_login_and_role_restrictions(client):
    hashed, salt = app.hash_password('Strong-password-123')
    with app.db_cursor(commit=True) as cur:
        cur.execute('INSERT INTO users(username,password_hash,salt,role,full_name) VALUES(?,?,?,?,?)', ('staff', hashed, salt, 'staff', 'Test Staff'))
    r = client.post('/admin/login', data={'username':'staff', 'password':'Strong-password-123'}, follow_redirects=False)
    assert r.status_code == 303
    assert 'HttpOnly' in r.headers['set-cookie']
    assert client.get('/admin').status_code == 200
    assert client.post('/admin/executive-orders/1/sign').status_code == 403
    assert client.get('/admin/audit-log').status_code == 403


def test_hr_registration_consumes_code(client):
    with app.db_cursor(commit=True) as cur:
        cur.execute('INSERT INTO hr_codes(code_hash,role) VALUES(?,?)', (app.hash_hr_code('TEST-CODE'), 'staff'))
    r = client.post('/admin/register', data={'code':'TEST-CODE'}, follow_redirects=False)
    from urllib.parse import urlparse, parse_qs
    token = parse_qs(urlparse(r.headers['location']).query)['token'][0]
    data = dict(token=token, full_name='Test User', national_id='TEST123', official_phone='123', personal_email='test@example.com', department='Office', appointment_date='2026-09-14', supervisor_name='Supervisor', role_detail='Staff', username='newstaff', password='Strong-password-123', confirm_password='Strong-password-123')
    assert client.post('/admin/register/details', data=data, follow_redirects=False).status_code == 303
    with app.db_cursor() as cur:
        cur.execute('SELECT is_used FROM hr_codes WHERE code_hash=?', (app.hash_hr_code('TEST-CODE'),))
        assert cur.fetchone()['is_used'] == 1
        cur.execute('SELECT password_hash FROM users WHERE username=?', ('newstaff',))
        assert cur.fetchone()['password_hash'] != data['password']
    r = client.post('/admin/register/details', data=data, follow_redirects=False)
    assert 'already' in r.headers['location']


def test_tampered_session_rejected():
    token = app.create_session_token(1, 'test', 'admin')
    assert app.verify_session_token(token)['role'] == 'admin'
    assert app.verify_session_token(token[:-8] + 'XXXXXXXX') is None


def test_user_input_is_escaped(client):
    response = client.get('/admin/login', params={'error':'<script>alert(1)</script>'})
    assert '<script>alert(1)</script>' not in response.text
    assert '&lt;script&gt;' in response.text


def test_health(client):
    assert client.get('/health').json()['status'] == 'ok'


def test_embedded_artwork_decodes():
    import base64
    for encoded in [app.PRES_SEAL_B64, app.VP_SEAL_B64, app.NAT_FLAG_B64]:
        assert base64.b64decode(encoded).startswith(b'\x89PNG\r\n\x1a\n')


def test_security_headers_and_sensitive_cache_policy(client):
    public = client.get('/')
    assert public.headers['x-content-type-options'] == 'nosniff'
    assert public.headers['x-frame-options'] == 'DENY'
    assert public.headers['referrer-policy'] == 'no-referrer'
    assert public.headers['permissions-policy'] == 'camera=(), geolocation=(), microphone=()'
    assert 'strict-transport-security' not in public.headers

    admin = client.get('/admin/login')
    assert admin.headers['cache-control'] == 'no-store, max-age=0'
    assert admin.headers['pragma'] == 'no-cache'


def test_cross_site_post_is_rejected(client):
    response = client.post(
        '/petition',
        headers={'origin': 'https://attacker.example'},
        data={
            'petitioner_name': 'Citizen',
            'email': 'citizen@example.com',
            'subject': 'Road',
            'message': 'Please review this road.',
        },
    )
    assert response.status_code == 403


def test_public_form_validation_rejects_bad_email_and_oversized_input(client):
    bad_email = client.post('/petition', data={
        'petitioner_name': 'Citizen', 'email': 'not-an-email',
        'subject': 'Road', 'message': 'Please review this road.',
    })
    assert bad_email.status_code == 422

    oversized = client.post('/petition', data={
        'petitioner_name': 'Citizen', 'email': 'citizen@example.com',
        'subject': 'R' * 201, 'message': 'Please review this road.',
    })
    assert oversized.status_code == 422


def test_database_backend_selection(monkeypatch):
    monkeypatch.setattr(app, 'DATABASE_URL', '')
    assert app.database_backend() == 'sqlite'
    monkeypatch.setattr(app, 'DATABASE_URL', 'postgresql://user:pass@db.example/president')
    assert app.database_backend() == 'postgresql'


def test_session_is_revalidated_against_current_account(client):
    hashed, salt = app.hash_password('Strong-password-123')
    with app.db_cursor(commit=True) as cur:
        cur.execute('INSERT INTO users(username,password_hash,salt,role,full_name) VALUES(?,?,?,?,?)',
                    ('temporary', hashed, salt, 'admin', 'Temporary Administrator'))
    assert client.post('/admin/login', data={
        'username': 'temporary', 'password': 'Strong-password-123'
    }, follow_redirects=False).status_code == 303
    assert client.get('/admin').status_code == 200
    with app.db_cursor(commit=True) as cur:
        cur.execute('UPDATE users SET username=? WHERE username=?', ('revoked-temporary', 'temporary'))
    revoked = client.get('/admin', follow_redirects=False)
    assert revoked.status_code == 303
    assert revoked.headers['location'] == '/admin/login'


def test_visit_request_validation(client):
    response = client.post('/visit', data={
        'requester_name': 'Citizen', 'email': 'invalid', 'phone': '',
        'organization': '', 'purpose': 'Courtesy visit',
        'requested_date': '2026-10-01', 'party_size': 1,
    })
    assert response.status_code == 422


def test_server_side_session_can_be_revoked(client):
    hashed, salt = app.hash_password('Strong-password-123')
    with app.db_cursor(commit=True) as cur:
        cur.execute('INSERT INTO users(username,password_hash,salt,role,full_name) VALUES(?,?,?,?,?)',
                    ('revocable', hashed, salt, 'admin', 'Revocable Administrator'))
    login = client.post('/admin/login', data={
        'username': 'revocable', 'password': 'Strong-password-123'
    }, follow_redirects=False)
    assert login.status_code == 303
    assert client.get('/admin').status_code == 200
    with app.db_cursor(commit=True) as cur:
        cur.execute('UPDATE sessions SET revoked_at=CURRENT_TIMESTAMP WHERE user_id=(SELECT id FROM users WHERE username=?)', ('revocable',))
    revoked = client.get('/admin', follow_redirects=False)
    assert revoked.status_code == 303
    assert revoked.headers['location'] == '/admin/login'


def test_expired_server_side_session_is_rejected(client):
    hashed, salt = app.hash_password('Strong-password-123')
    with app.db_cursor(commit=True) as cur:
        cur.execute('INSERT INTO users(username,password_hash,salt,role,full_name) VALUES(?,?,?,?,?)',
                    ('expired', hashed, salt, 'admin', 'Expired Administrator'))
    login = client.post('/admin/login', data={
        'username': 'expired', 'password': 'Strong-password-123'
    }, follow_redirects=False)
    assert login.status_code == 303
    with app.db_cursor(commit=True) as cur:
        cur.execute("UPDATE sessions SET expires_at='2000-01-01 00:00:00' WHERE user_id=(SELECT id FROM users WHERE username=?)", ('expired',))
    expired = client.get('/admin', follow_redirects=False)
    assert expired.status_code == 303
    assert expired.headers['location'] == '/admin/login'
