"""Security and backup changes salvaged from PR #3 (kept on SQLite)."""
import asyncio
import contextlib
import io
import sys
from datetime import datetime, timedelta
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ung_president as app
import president_backup

HOST = "testserver"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.delenv("UNG_PRESIDENT_TRUSTED_ORIGINS", raising=False)
    monkeypatch.delenv("UNG_PRESIDENT_PUBLIC_URL", raising=False)
    app.DB_PATH = str(tmp_path / "test.db")
    app._rate_buckets.clear()
    with contextlib.redirect_stdout(io.StringIO()):
        with TestClient(app.app) as c:
            # If an earlier test loaded the password-reset add-on, give this fresh
            # database the column it adds at startup on the real site.
            if "password_reset" in sys.modules:
                sys.modules["password_reset"]._ensure_schema()
            yield c


def make_user(username="staff", role="admin"):
    hashed, salt = app.hash_password("Strong-password-123")
    with app.db_cursor(commit=True) as cur:
        cur.execute("INSERT INTO users(username,password_hash,salt,role,full_name) VALUES(?,?,?,?,?)",
                    (username, hashed, salt, role, "Test User"))


def signed_in(client):
    return client.get("/admin", follow_redirects=False).status_code == 200


def login(client, username="staff"):
    r = client.post("/admin/login", data={"username": username, "password": "Strong-password-123"},
                    follow_redirects=False)
    assert r.status_code == 303


# --- session re-check ---------------------------------------------------

def test_deleted_account_loses_access_immediately(client):
    make_user(); login(client)
    assert signed_in(client)
    with app.db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM audit_log")  # audit rows reference the user
        cur.execute("DELETE FROM users WHERE username='staff'")
    assert not signed_in(client)


def test_replaced_account_with_reused_id_is_not_trusted(client):
    make_user(); login(client)
    with app.db_cursor(commit=True) as cur:
        cur.execute("UPDATE users SET username='someone-else' WHERE username='staff'")
    assert not signed_in(client)


def test_role_comes_from_database_not_cookie(client):
    make_user(role="admin"); login(client)
    assert signed_in(client)
    req = type("R", (), {"cookies": client.cookies})()
    assert app.get_current_user(req)["role"] == "admin"
    with app.db_cursor(commit=True) as cur:
        cur.execute("UPDATE users SET role='staff' WHERE username='staff'")
    assert app.get_current_user(req)["role"] == "staff"


def test_locked_account_loses_access(client):
    make_user(); login(client)
    until = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
    with app.db_cursor(commit=True) as cur:
        cur.execute("UPDATE users SET locked_until=? WHERE username='staff'", (until,))
    assert not signed_in(client)


# --- cross-site form posts ----------------------------------------------

PETITION = {"petitioner_name": "Jane", "email": "jane@example.ug", "subject": "Roads", "message": "Please fix."}


@pytest.mark.parametrize("origin,expected", [
    (None, 303),                       # non-browser client
    (f"http://{HOST}", 303),           # same site
    ("https://evil.example", 403),     # another site
    ("null", 403),                     # opaque origin
])
def test_cross_site_posts_are_rejected(client, origin, expected):
    headers = {"origin": origin} if origin else {}
    r = client.post("/petition", data=PETITION, headers=headers, follow_redirects=False)
    assert r.status_code == expected


def test_configured_public_site_is_trusted(client, monkeypatch):
    monkeypatch.setenv("UNG_PRESIDENT_PUBLIC_URL", "https://statehouse.example.ug")
    r = client.post("/petition", data=PETITION, headers={"origin": "https://statehouse.example.ug"},
                    follow_redirects=False)
    assert r.status_code == 303


def test_referrer_policy_keeps_browser_origin_header_usable(client):
    # 'no-referrer' makes browsers send Origin: null on every form post, which the
    # cross-site check above would reject, locking everyone out.
    assert client.get("/").headers["referrer-policy"] == "strict-origin-when-cross-origin"


# --- headers --------------------------------------------------------------

def test_private_pages_are_never_cached(client):
    r = client.get("/admin/login")
    assert r.headers["cache-control"] == "no-store, max-age=0"
    assert "camera=()" in r.headers["permissions-policy"]
    assert "cache-control" not in client.get("/").headers


# --- public form validation ----------------------------------------------

def test_petition_rejects_bad_email_and_oversized_text(client):
    assert client.post("/petition", data=dict(PETITION, email="not-an-email")).status_code == 422
    assert client.post("/petition", data=dict(PETITION, message="x" * 5001)).status_code == 422
    assert client.post("/petition", data=dict(PETITION, subject="   ")).status_code == 422


def test_visit_request_rejects_bad_party_size(client):
    form = {"requester_name": "Jane", "email": "jane@example.ug", "purpose": "Tour",
            "requested_date": "2026-11-01", "party_size": "0"}
    assert client.post("/visit", data=form).status_code == 422
    form["party_size"] = "4"
    assert client.post("/visit", data=form, follow_redirects=False).status_code == 303


# --- backup ---------------------------------------------------------------

def test_backup_covers_every_table_except_login_material(client):
    import president_nsc, president_executive_suite, password_reset  # noqa: F401  create add-on tables
    president_nsc.apply_nsc(app); president_executive_suite.apply_executive_suite(app)
    with contextlib.redirect_stdout(io.StringIO()):
        with TestClient(app.app):
            pass
    tables = president_backup.backup_tables(app.db_cursor)
    assert {"users", "petitions", "audit_log", "nsc_records", "executive_archive"} <= set(tables)
    assert not set(tables) & president_backup.EXCLUDED_TABLES


def test_backup_is_a_no_op_without_configuration(monkeypatch):
    monkeypatch.delenv("BACKUP_SERVICE_URL", raising=False)
    monkeypatch.delenv("BACKUP_SYNC_TOKEN", raising=False)
    assert president_backup.start_backup_worker(app.db_cursor) is False


def test_backup_pushes_each_table_with_token(client, monkeypatch):
    make_user()
    client.post("/petition", data=PETITION)
    sent = []

    def handler(request):
        sent.append((request.headers["x-backup-token"], request.read()))
        return httpx.Response(200, json={"ok": True})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(president_backup.httpx, "AsyncClient",
                        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))
    monkeypatch.setenv("BACKUP_SERVICE_URL", "https://backup.example")
    monkeypatch.setenv("BACKUP_SYNC_TOKEN", "t0ken")
    result = asyncio.run(president_backup.sync_backup_snapshot(app.db_cursor))
    assert result["status"] == "ok"
    assert result["tables"] == len(sent) >= 2
    assert all(tok == "t0ken" for tok, _ in sent)
    assert result["records"] >= 2  # the user and the petition
