import contextlib
import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ung_president as app


EXPANDED_ROUTES = [
    ("Citizens Abroad", "/admin/citizens-abroad"),
    ("Travel Advisories", "/admin/travel-advisories"),
    ("Emergency Alerts", "/admin/emergency-alerts"),
    ("Missions", "/admin/missions"),
    ("Consular Queue", "/admin/consular"),
    ("Media Accreditation", "/admin/media-accreditation"),
    ("Attestations", "/admin/attestations"),
    ("Treaties / Archive", "/admin/treaties"),
    ("Approvals", "/admin/approvals"),
    ("Biometrics", "/admin/biometrics"),
]


@pytest.fixture
def client(tmp_path):
    app.DB_PATH = str(tmp_path / "expanded-test.db")
    app._rate_buckets.clear()
    app.init_db()
    import registration_response_fix
    registration_response_fix.apply_registration_response_fix()
    import president_expanded_admin
    president_expanded_admin.apply_expanded_admin()
    with contextlib.redirect_stdout(io.StringIO()):
        with TestClient(app.app) as c:
            yield c


def _login_admin(client):
    hashed, salt = app.hash_password("Strong-password-123")
    with app.db_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO users(username,password_hash,salt,role,full_name) VALUES(?,?,?,?,?)",
            ("expanded-admin", hashed, salt, "admin", "Expanded Admin"),
        )
    response = client.post(
        "/admin/login",
        data={"username": "expanded-admin", "password": "Strong-password-123"},
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_expanded_admin_routes_require_authentication(client):
    for _, path in EXPANDED_ROUTES:
        assert client.get(path).status_code in {401, 403}, path


def test_admin_dashboard_exposes_all_expanded_modules(client):
    _login_admin(client)
    response = client.get("/admin")
    assert response.status_code == 200
    for label, path in EXPANDED_ROUTES:
        assert label in response.text, label
        assert path in response.text, path


def test_authenticated_admin_can_open_all_expanded_modules(client):
    _login_admin(client)
    for _, path in EXPANDED_ROUTES:
        response = client.get(path)
        assert response.status_code == 200, (path, response.status_code)
