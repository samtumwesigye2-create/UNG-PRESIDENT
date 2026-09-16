import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ung_president as app
from fastapi.testclient import TestClient


def test_staff_login_exposes_password_reset_and_reset_route(tmp_path):
    app.DB_PATH = str(tmp_path / "reset.db")
    app._rate_buckets.clear()
    with contextlib.redirect_stdout(io.StringIO()):
        with TestClient(app.app) as client:
            login = client.get("/admin/login")
            assert login.status_code == 200
            assert 'href="/admin/password-reset"' in login.text

            reset = client.get("/admin/password-reset")
            assert reset.status_code == 200
            assert "Reset Staff Password" in reset.text


def test_password_reset_changes_password_and_rejects_token_reuse(tmp_path):
    app.DB_PATH = str(tmp_path / "reset.db")
    app._rate_buckets.clear()
    with contextlib.redirect_stdout(io.StringIO()):
        with TestClient(app.app) as client:
            old_hash, salt = app.hash_password("Old-password-123!")
            with app.db_cursor(commit=True) as cur:
                cur.execute(
                    "INSERT INTO users(username,password_hash,salt,role,full_name,personal_email) VALUES(?,?,?,?,?,?)",
                    ("staff", old_hash, salt, "staff", "Test Staff", "recovery@example.com"),
                )

            token = app.create_password_reset_token("staff", "recovery@example.com")
            response = client.post(
                "/admin/password-reset/complete",
                data={
                    "token": token,
                    "password": "New-password-456!",
                    "confirm_password": "New-password-456!",
                },
                follow_redirects=False,
            )
            assert response.status_code == 303

            with app.db_cursor() as cur:
                cur.execute("SELECT password_hash,salt FROM users WHERE username=?", ("staff",))
                row = cur.fetchone()
            assert app.verify_password("New-password-456!", row["password_hash"], row["salt"])
            assert not app.verify_password("Old-password-123!", row["password_hash"], row["salt"])

            reused = client.post(
                "/admin/password-reset/complete",
                data={
                    "token": token,
                    "password": "Another-password-789!",
                    "confirm_password": "Another-password-789!",
                },
                follow_redirects=False,
            )
            assert reused.status_code in (400, 303)
            assert reused.headers.get("location") != "/admin/login?reset=success"
