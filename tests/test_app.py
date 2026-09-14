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
