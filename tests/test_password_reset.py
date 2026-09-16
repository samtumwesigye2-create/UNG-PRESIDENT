import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import password_reset as reset
from fastapi.testclient import TestClient

app = reset.core


def _register_staff(client):
    with app.db_cursor(commit=True) as cur:
        cur.execute('INSERT INTO hr_codes(code_hash,role) VALUES(?,?)', (app.hash_hr_code('RESET-CODE'), 'staff'))
    response = client.post('/admin/register', data={'code':'RESET-CODE'}, follow_redirects=False)
    from urllib.parse import urlparse, parse_qs
    token = parse_qs(urlparse(response.headers['location']).query)['token'][0]
    data = dict(token=token, full_name='Test Staff', national_id='RESET123', official_phone='123', personal_email='recovery@example.com', department='Office', appointment_date='2026-09-15', supervisor_name='Supervisor', role_detail='Staff', username='staff', password='Old-password-123!', confirm_password='Old-password-123!')
    assert client.post('/admin/register/details', data=data, follow_redirects=False).status_code == 303


def test_staff_login_exposes_password_reset_and_reset_route(tmp_path):
    app.DB_PATH = str(tmp_path / 'reset.db')
    app._rate_buckets.clear()
    with contextlib.redirect_stdout(io.StringIO()):
        with TestClient(app.app) as client:
            login = client.get('/admin/login')
            assert login.status_code == 200
            assert 'href="/admin/password-reset"' in login.text
            page = client.get('/admin/password-reset')
            assert page.status_code == 200
            assert 'Reset Staff Password' in page.text


def test_password_reset_changes_password_and_rejects_token_reuse(tmp_path):
    app.DB_PATH = str(tmp_path / 'reset.db')
    app._rate_buckets.clear()
    with contextlib.redirect_stdout(io.StringIO()):
        with TestClient(app.app) as client:
            _register_staff(client)
            token = reset.create_password_reset_token('staff', 'recovery@example.com')
            assert token
            response = client.post('/admin/password-reset/complete', data={'token':token, 'password':'New-password-456!', 'confirm_password':'New-password-456!'}, follow_redirects=False)
            assert response.status_code == 303
            with app.db_cursor() as cur:
                cur.execute('SELECT password_hash,salt FROM users WHERE username=?', ('staff',))
                row = cur.fetchone()
            assert app.verify_password('New-password-456!', row['password_hash'], row['salt'])
            assert not app.verify_password('Old-password-123!', row['password_hash'], row['salt'])
            reused = client.post('/admin/password-reset/complete', data={'token':token, 'password':'Another-password-789!', 'confirm_password':'Another-password-789!'}, follow_redirects=False)
            assert reused.status_code == 400
