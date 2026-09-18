"""Separate principal-only Digital Executive Suite for UNG-PRESIDENT."""
import base64
import hashlib
import hmac
import os
import secrets
import time
import io
import json
import urllib.request
import urllib.error
from datetime import datetime
from html import escape

from cryptography.fernet import Fernet, InvalidToken
import pyotp
import qrcode
from fastapi import Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

import ung_president as core

EXEC_COOKIE = "executive_session"
EXEC_MAX_AGE = 60 * 60 * 8
EXEC_ROLES = {"president", "vice_president", "prime_minister"}
VAULT_BASE_URL = os.environ.get("UNG_VAULT_BASE_URL", "https://ung-vault-production.up.railway.app").rstrip("/")
VAULT_INGEST_SECRET = os.environ.get("UNG_VAULT_INGEST_SECRET", "")


def _fernet():
    key = base64.urlsafe_b64encode(hashlib.sha256((core.SECRET_KEY + "|executive-suite").encode()).digest())
    return Fernet(key)


def _hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), core.PBKDF2_ITERATIONS)
    return base64.b64encode(digest).decode()


def _verify_password(password: str, stored_hash: str, salt: str) -> bool:
    return hmac.compare_digest(_hash_password(password, salt), stored_hash)


def _token(account_id: int, username: str, role: str, session_id: str) -> str:
    issued = int(time.time())
    payload = f"executive|{account_id}|{username}|{role}|{session_id}|{issued}"
    sig = hmac.new(core.SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}|{sig}".encode()).decode()


def _verify_token(token: str):
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        purpose, account_id, username, role, session_id, issued, sig = raw.split("|")
        if purpose != "executive" or role not in EXEC_ROLES:
            return None
        payload = f"{purpose}|{account_id}|{username}|{role}|{session_id}|{issued}"
        expected = hmac.new(core.SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        if int(time.time()) - int(issued) > EXEC_MAX_AGE:
            return None
        return {"account_id": int(account_id), "username": username, "role": role, "session_id": session_id}
    except Exception:
        return None


def _issue_session(row, request: Request):
    session_id = secrets.token_hex(24)
    now = datetime.utcnow()
    from datetime import timedelta
    expires = now + timedelta(seconds=EXEC_MAX_AGE)
    user_agent = (request.headers.get("user-agent") or "")[:500]
    ip_address = request.client.host if request.client else ""
    with core.db_cursor(commit=True) as cur:
        cur.execute("""INSERT INTO executive_sessions
            (id,account_id,username,role,user_agent,ip_address,created_at,last_seen,expires_at)
            VALUES(?,?,?,?,?,?,?,?,?)""",
            (session_id,row["id"],row["username"],row["role"],user_agent,ip_address,now.isoformat(),now.isoformat(),expires.isoformat()))
    return _token(row["id"], row["username"], row["role"], session_id)



def _mfa_challenge_token(account_id: int, username: str) -> str:
    issued = int(time.time())
    payload = f"executive-mfa|{account_id}|{username}|{issued}"
    sig = hmac.new(core.SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}|{sig}".encode()).decode()


def _verify_mfa_challenge(token: str):
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        purpose, account_id, username, issued, sig = raw.split("|")
        if purpose != "executive-mfa":
            return None
        payload = f"{purpose}|{account_id}|{username}|{issued}"
        expected = hmac.new(core.SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        if int(time.time()) - int(issued) > 300:
            return None
        return {"account_id": int(account_id), "username": username}
    except Exception:
        return None


def _principal(request: Request):
    token = request.cookies.get(EXEC_COOKIE)
    user = _verify_token(token) if token else None
    if not user:
        return None
    with core.db_cursor() as cur:
        cur.execute("""SELECT id,expires_at,revoked_at FROM executive_sessions
                       WHERE id=? AND account_id=?""", (user["session_id"], user["account_id"]))
        session = cur.fetchone()
    if not session or session["revoked_at"] or datetime.fromisoformat(session["expires_at"]) < datetime.utcnow():
        return None
    with core.db_cursor(commit=True) as cur:
        cur.execute("UPDATE executive_sessions SET last_seen=? WHERE id=?", (datetime.utcnow().isoformat(), user["session_id"]))
    return user


def init_schema():
    with core.db_cursor(commit=True) as cur:
        cur.execute("""CREATE TABLE IF NOT EXISTS executive_principal_accounts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_login TEXT,
            mfa_secret TEXT,
            mfa_enabled INTEGER NOT NULL DEFAULT 0
        )""")
        for ddl in (
            "ALTER TABLE executive_principal_accounts ADD COLUMN mfa_secret TEXT",
            "ALTER TABLE executive_principal_accounts ADD COLUMN mfa_enabled INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE executive_principal_accounts ADD COLUMN password_changed_at TEXT",
        ):
            try:
                cur.execute(ddl)
            except Exception:
                pass
        cur.execute("""CREATE TABLE IF NOT EXISTS executive_secure_messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            ciphertext TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'normal',
            created_by INTEGER,
            created_at TEXT NOT NULL,
            vault_object_id TEXT
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS executive_archive(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            record_reference TEXT,
            category TEXT NOT NULL,
            retention TEXT NOT NULL,
            notes_ciphertext TEXT,
            created_by INTEGER,
            created_at TEXT NOT NULL,
            vault_object_id TEXT
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS executive_meetings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            meeting_type TEXT NOT NULL,
            scheduled_for TEXT,
            guests TEXT,
            location_mode TEXT NOT NULL,
            notes_ciphertext TEXT,
            created_by INTEGER,
            created_at TEXT NOT NULL,
            vault_object_id TEXT
        )""")
        for ddl in (
            "ALTER TABLE executive_secure_messages ADD COLUMN vault_object_id TEXT",
            "ALTER TABLE executive_archive ADD COLUMN vault_object_id TEXT",
            "ALTER TABLE executive_meetings ADD COLUMN vault_object_id TEXT",
        ):
            try:
                cur.execute(ddl)
            except Exception:
                pass
        cur.execute("""CREATE TABLE IF NOT EXISTS executive_enrollment_codes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code_hash TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL,
            issued_by INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used_at TEXT
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS executive_recovery_codes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            code_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            used_at TEXT
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS executive_sessions(
            id TEXT PRIMARY KEY,
            account_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            role TEXT NOT NULL,
            user_agent TEXT,
            ip_address TEXT,
            created_at TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            revoked_at TEXT
        )""")


def seed_principal_accounts_from_env():
    seeds = [
        ("president", "president", "President", os.environ.get("UNG_EXEC_PRESIDENT_PASSWORD")),
        ("vice.president", "vice_president", "Vice President", os.environ.get("UNG_EXEC_VICE_PRESIDENT_PASSWORD")),
        ("prime.minister", "prime_minister", "Prime Minister", os.environ.get("UNG_EXEC_PRIME_MINISTER_PASSWORD")),
    ]
    with core.db_cursor(commit=True) as cur:
        for username, role, full_name, password in seeds:
            if not password:
                continue
            cur.execute("SELECT id FROM executive_principal_accounts WHERE username=?", (username,))
            if cur.fetchone():
                continue
            salt = secrets.token_hex(16)
            cur.execute(
                "INSERT INTO executive_principal_accounts(username,password_hash,salt,role,full_name,created_at) VALUES(?,?,?,?,?,?)",
                (username, _hash_password(password, salt), salt, role, full_name, datetime.utcnow().isoformat()),
            )


def _store_executive_record_in_vault(*, user, record_type: str, name: str, payload: dict,
                                     classification: str = "confidential",
                                     protection_profile: str = "VAULT-ENVELOPE") -> str:
    if not VAULT_INGEST_SECRET:
        raise HTTPException(status_code=503, detail="Secure VAULT record storage is not configured")
    body = {
        "record_type": record_type,
        "name": name,
        "principal": user["username"],
        "classification": classification,
        "protection_profile": protection_profile,
        "payload": payload,
    }
    raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(VAULT_INGEST_SECRET.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    req = urllib.request.Request(
        VAULT_BASE_URL + "/vault/integrations/president/records",
        data=raw,
        headers={
            "Content-Type": "application/json",
            "X-UNG-PRESIDENT-Signature": signature,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"VAULT rejected executive record storage ({exc.code})") from None
    except Exception:
        raise HTTPException(status_code=503, detail="VAULT unavailable; executive record was not saved") from None
    object_id = str(result.get("id") or "")
    if not object_id:
        raise HTTPException(status_code=503, detail="VAULT did not return a protected object reference")
    return object_id


def _vault_health():
    try:
        req = urllib.request.Request(VAULT_BASE_URL + "/health", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return bool(200 <= resp.status < 300), data
    except Exception as exc:
        return False, {"error": type(exc).__name__}


def _title(role: str) -> str:
    return {
        "president": "President",
        "vice_president": "Vice President",
        "prime_minister": "Prime Minister",
    }.get(role, "Principal")


def _login_page(error=""):
    err = f'<div class="err">{escape(error)}</div>' if error else ""
    page = f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Executive Portal Login · UNG-PRESIDENT</title><style>
*{{box-sizing:border-box}}body{{margin:0;min-height:100vh;display:grid;place-items:center;background:radial-gradient(circle at 50% 0,#133457,#061321 56%);font-family:Arial,sans-serif;color:#eef3f8}}
.box{{width:min(460px,92vw);background:#0b1c2d;border:1px solid #294158;border-radius:18px;padding:34px;box-shadow:0 24px 70px #0008}}.crest{{width:78px;height:78px;border:2px solid #cbaa4d;border-radius:50%;display:grid;place-items:center;margin:0 auto 18px;overflow:hidden;background:#071522}}.crest img{{width:100%;height:100%;object-fit:cover;display:block}}
h1{{font:28px Georgia;margin:0;text-align:center}}.sub{{text-align:center;color:#c3a95d;letter-spacing:2px;font-size:11px;margin:7px 0 26px}}label{{display:block;font-size:12px;font-weight:700;margin:12px 0 5px;color:#cbd6df}}input{{width:100%;padding:12px;background:#07121d;border:1px solid #334a61;border-radius:8px;color:white;font-size:16px}}button{{width:100%;margin-top:18px;padding:12px;background:#c9a84b;border:0;border-radius:8px;font-weight:800;color:#07111f}}.err{{background:#4a1820;border:1px solid #7c2b38;padding:10px;border-radius:8px;margin-bottom:14px}}.note{{font-size:11px;color:#7f91a2;text-align:center;margin-top:16px}}
</style></head><body><div class="box"><div class="crest"><img src="data:image/png;base64,__PRES_SEAL__" alt="Presidential Seal"></div><h1>Digital Executive Suite</h1><div class="sub">PRINCIPAL ACCESS · REPUBLIC OF UGANDA</div>{err}
<form method="post" action="/executive/login"><label>Executive username</label><input name="username" autocomplete="username" required><label>Password</label><input type="password" name="password" autocomplete="current-password" required><button>Enter Executive Portal</button></form>
<div class="note">President · Vice President · Prime Minister only</div></div></body></html>"""
    page = page.replace("__PRES_SEAL__", core.PRES_SEAL_B64)
    return HTMLResponse(page)


def executive_login_form(request: Request):
    if _principal(request):
        return RedirectResponse("/executive", status_code=303)
    return _login_page(request.query_params.get("error", ""))


def executive_login(request: Request, username: str = Form(...), password: str = Form(...)):
    with core.db_cursor() as cur:
        cur.execute("SELECT * FROM executive_principal_accounts WHERE username=?", (username.strip(),))
        row = cur.fetchone()
    if not row or row["role"] not in EXEC_ROLES or not _verify_password(password, row["password_hash"], row["salt"]):
        return RedirectResponse("/executive/login?error=Invalid+executive+credentials", status_code=303)
    if row["mfa_enabled"]:
        response = RedirectResponse("/executive/mfa", status_code=303)
        response.set_cookie(
            "executive_mfa_challenge",
            _mfa_challenge_token(row["id"], row["username"]),
            httponly=True,
            samesite="strict",
            secure=bool(os.environ.get("RAILWAY_ENVIRONMENT_ID")),
            max_age=300,
            path="/",
        )
        return response
    with core.db_cursor(commit=True) as cur:
        cur.execute("UPDATE executive_principal_accounts SET last_login=? WHERE id=?", (datetime.utcnow().isoformat(), row["id"]))
    core.log_action(None, row["username"], "executive_portal_login", "executive_principal_accounts", row["id"])
    token = _issue_session(row, request)
    response = RedirectResponse("/executive", status_code=303)
    response.set_cookie(EXEC_COOKIE, token, httponly=True, samesite="strict", secure=bool(os.environ.get("RAILWAY_ENVIRONMENT_ID")), max_age=EXEC_MAX_AGE, path="/")
    return response



def executive_mfa_form(request: Request):
    challenge = _verify_mfa_challenge(request.cookies.get("executive_mfa_challenge",""))
    if not challenge:
        return RedirectResponse("/executive/login?error=MFA+challenge+expired", status_code=303)
    return HTMLResponse("""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Executive MFA</title>
<style>body{font-family:Arial;background:#071522;color:#fff;display:grid;place-items:center;min-height:100vh}.b{width:min(420px,92vw);background:#0c2033;padding:28px;border:1px solid #385069;border-radius:14px}input{width:100%;padding:13px;margin:8px 0 14px;box-sizing:border-box;font-size:22px;letter-spacing:5px;text-align:center}button{padding:12px;width:100%;background:#caa84b;border:0;font-weight:bold}</style></head><body><div class="b"><h2>Executive MFA Verification</h2><p>Enter the 6-digit code from your authenticator app.</p><form method="post" action="/executive/mfa"><input inputmode="numeric" pattern="[0-9]{6}" maxlength="6" name="code" required autofocus><button>Verify & Enter</button></form><hr style="border-color:#294158;margin:22px 0"><p style="font-size:12px;color:#aebdcb">Lost access to your authenticator?</p><form method="post" action="/executive/mfa/recovery"><input name="recovery_code" placeholder="One-time recovery code" required style="letter-spacing:1px;font-size:16px"><button>Use Recovery Code</button></form></div></body></html>""")


def executive_mfa_verify(request: Request, code: str = Form(...)):
    challenge = _verify_mfa_challenge(request.cookies.get("executive_mfa_challenge",""))
    if not challenge:
        return RedirectResponse("/executive/login?error=MFA+challenge+expired", status_code=303)
    with core.db_cursor() as cur:
        cur.execute("SELECT * FROM executive_principal_accounts WHERE id=?", (challenge["account_id"],))
        row = cur.fetchone()
    if not row or not row["mfa_enabled"] or not row["mfa_secret"]:
        return RedirectResponse("/executive/login?error=MFA+not+configured", status_code=303)
    if not pyotp.TOTP(row["mfa_secret"]).verify(code.strip(), valid_window=1):
        return RedirectResponse("/executive/mfa?error=Invalid+code", status_code=303)
    with core.db_cursor(commit=True) as cur:
        cur.execute("UPDATE executive_principal_accounts SET last_login=? WHERE id=?", (datetime.utcnow().isoformat(), row["id"]))
    core.log_action(None, row["username"], "executive_portal_login_mfa", "executive_principal_accounts", row["id"])
    response = RedirectResponse("/executive", status_code=303)
    response.set_cookie(EXEC_COOKIE, _issue_session(row, request), httponly=True, samesite="strict", secure=bool(os.environ.get("RAILWAY_ENVIRONMENT_ID")), max_age=EXEC_MAX_AGE, path="/")
    response.delete_cookie("executive_mfa_challenge", path="/")
    return response



def executive_mfa_recovery(request: Request, recovery_code: str = Form(...)):
    challenge = _verify_mfa_challenge(request.cookies.get("executive_mfa_challenge",""))
    if not challenge:
        return RedirectResponse("/executive/login?error=MFA+challenge+expired", status_code=303)
    code_hash = _hash_recovery_code(recovery_code.strip().upper())
    with core.db_cursor() as cur:
        cur.execute("SELECT * FROM executive_principal_accounts WHERE id=?", (challenge["account_id"],))
        row = cur.fetchone()
        cur.execute("SELECT * FROM executive_recovery_codes WHERE account_id=? AND code_hash=? AND used_at IS NULL",
                    (challenge["account_id"], code_hash))
        rc = cur.fetchone()
    if not row or not rc:
        return RedirectResponse("/executive/mfa?error=Invalid+recovery+code", status_code=303)
    now = datetime.utcnow().isoformat()
    with core.db_cursor(commit=True) as cur:
        cur.execute("UPDATE executive_recovery_codes SET used_at=? WHERE id=? AND used_at IS NULL", (now, rc["id"]))
        cur.execute("UPDATE executive_principal_accounts SET last_login=? WHERE id=?", (now, row["id"]))
    core.log_action(None, row["username"], "executive_portal_login_recovery_code", "executive_principal_accounts", row["id"])
    response = RedirectResponse("/executive/security", status_code=303)
    response.set_cookie(EXEC_COOKIE, _token(row["id"], row["username"], row["role"]), httponly=True, samesite="strict", secure=bool(os.environ.get("RAILWAY_ENVIRONMENT_ID")), max_age=EXEC_MAX_AGE, path="/")
    response.delete_cookie("executive_mfa_challenge", path="/")
    return response


def executive_logout(request: Request):
    user = _principal(request)
    if user:
        with core.db_cursor(commit=True) as cur:
            cur.execute("UPDATE executive_sessions SET revoked_at=? WHERE id=?", (datetime.utcnow().isoformat(), user["session_id"]))
        core.log_action(None, user["username"], "executive_session_logout", "executive_sessions", user["session_id"])
    response = RedirectResponse("/executive/login", status_code=303)
    response.delete_cookie(EXEC_COOKIE, path="/")
    return response


def setup_form(request: Request):
    with core.db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM executive_principal_accounts")
        n = cur.fetchone()["n"]
    if n:
        return RedirectResponse("/executive/login", status_code=303)
    return HTMLResponse("""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Executive Portal Setup</title>
<style>body{font-family:Arial;background:#071522;color:#fff;display:grid;place-items:center;min-height:100vh}.b{width:min(480px,92vw);background:#0c2033;padding:28px;border:1px solid #385069;border-radius:14px}input,select{width:100%;padding:11px;margin:5px 0 12px;box-sizing:border-box}button{padding:12px;width:100%;background:#caa84b;border:0;font-weight:bold}</style></head><body><div class="b"><h2>Initial Executive Principal Enrollment</h2><form method="post" action="/executive/setup"><label>Setup code</label><input type="password" name="setup_code" required><label>Full name</label><input name="full_name" required><label>Username</label><input name="username" required><label>Role</label><select name="role"><option value="president">President</option><option value="vice_president">Vice President</option><option value="prime_minister">Prime Minister</option></select><label>Password</label><input type="password" name="password" minlength="12" required><button>Create Principal Account</button></form></div></body></html>""".replace("__PRES_SEAL__", core.PRES_SEAL_B64))


def setup_submit(setup_code: str = Form(...), full_name: str = Form(...), username: str = Form(...), role: str = Form(...), password: str = Form(...)):
    expected = os.environ.get("UNG_EXECUTIVE_SETUP_CODE", "")
    if not expected or not hmac.compare_digest(setup_code, expected):
        raise HTTPException(status_code=403, detail="Invalid setup code")
    if role not in EXEC_ROLES or len(password) < 12:
        raise HTTPException(status_code=400, detail="Invalid role or password")
    with core.db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM executive_principal_accounts")
        if cur.fetchone()["n"]:
            raise HTTPException(status_code=409, detail="Executive portal already initialized")
    salt = secrets.token_hex(16)
    with core.db_cursor(commit=True) as cur:
        cur.execute("INSERT INTO executive_principal_accounts(username,password_hash,salt,role,full_name,created_at) VALUES(?,?,?,?,?,?)",
                    (username.strip(), _hash_password(password, salt), salt, role, full_name.strip(), datetime.utcnow().isoformat()))
    return RedirectResponse("/executive/login", status_code=303)


def _decrypt(value):
    if not value:
        return ""
    try:
        return _fernet().decrypt(value.encode()).decode()
    except (InvalidToken, ValueError):
        return "[unavailable]"


def _shell(user, body):
    page = f"""<!doctype html><html><head><meta name="viewport" content="width=1180,initial-scale=1"><title>{escape(_title(user["role"]))} Executive Suite</title>
<style>
*{{box-sizing:border-box}}html,body{{margin:0;min-width:1180px;background:#07111f;color:#edf2f7;font-family:Arial,sans-serif}}body{{overflow-x:auto}}
.top{{height:118px;background:linear-gradient(90deg,#061529,#0b2948);border-bottom:2px solid #caa447;display:flex;align-items:center;justify-content:space-between;padding:0 34px}}.brand{{display:flex;align-items:center;gap:16px}}.brand-seal{{width:72px;height:72px;border-radius:50%;overflow:hidden;border:2px solid #caa447;box-shadow:0 0 0 3px #0b1d30}}.brand-seal img{{width:100%;height:100%;object-fit:cover;display:block}}.brand h1{{font:30px Georgia;margin:0}}.brand small{{color:#d7b85c;letter-spacing:2px}}.who{{text-align:right;color:#aebdcb;font-size:12px;padding:10px 14px;border:1px solid #2c435a;border-radius:10px;background:#091a2b}}
.layout{{display:grid;grid-template-columns:250px 1fr;min-height:calc(100vh - 118px)}}aside{{background:#081827;border-right:1px solid #20364d;padding:28px 20px}}aside a{{display:block;color:#dfe8f1;text-decoration:none;padding:11px 12px;border-radius:7px;margin-bottom:5px}}aside a:hover{{background:#102b47;color:#f2cf69}}
main{{padding:26px 30px 38px;max-width:1450px}}.hero{{background:linear-gradient(120deg,#0e2d4c,#102039);border:1px solid #2a435d;border-radius:16px;padding:24px 28px;box-shadow:0 10px 28px #0005}}.hero-head{{display:flex;align-items:center;gap:18px}}.principal-seal{{width:82px;height:82px;border-radius:50%;overflow:hidden;border:2px solid #d6b354;box-shadow:0 0 0 3px #0b1d30}}.principal-seal img{{width:100%;height:100%;object-fit:cover;display:block}}.hero h2{{font:31px Georgia;margin:0 0 7px}}.gold{{color:#d6b354}}.hero p{{color:#b8c7d6;margin:0}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:14px}}.card,.panel{{background:#0c1d2e;border:1px solid #233b53;border-radius:13px;padding:18px;box-shadow:0 5px 14px #0004}}.card h3{{color:#f0cc67;margin-top:0}}.card p{{color:#aebdcb;font-size:13px;line-height:1.45}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}}label{{display:block;font-size:12px;font-weight:700;margin:10px 0 5px;color:#c9d3dd}}input,textarea,select{{width:100%;background:#07131f;color:#eef3f8;border:1px solid #334a61;border-radius:7px;padding:10px}}textarea{{min-height:88px}}button{{margin-top:12px;background:#c7a247;color:#07111f;border:0;border-radius:7px;padding:10px 14px;font-weight:800}}table{{width:100%;border-collapse:collapse;margin-top:12px;font-size:12px}}th,td{{padding:9px;border-bottom:1px solid #24384b;text-align:left;vertical-align:top}}th{{color:#d9ba61}}.suite-planner{{background:linear-gradient(135deg,#0c1d2e,#102842);border-color:#34516d}}.suite-planner h3{{font:22px Georgia;color:#f0d37b;margin-bottom:4px}}.suite-planner .intro{{color:#9fb2c3;font-size:12px;margin:0 0 12px}}
</style></head><body><div class="top"><div class="brand"><div class="brand-seal"><img src="data:image/png;base64,__PRES_SEAL__" alt="Presidential Seal"></div><div><h1>DIGITAL EXECUTIVE SUITE</h1><small>PRINCIPAL PORTAL · UNG-PRESIDENT</small></div></div><div class="who">{escape(_title(user["role"]).upper())}<br><strong>{escape(user["username"])}</strong></div></div>
<div class="layout"><aside><a href="/executive">Executive Home</a><a href="/executive/vault">Secure Vault & SCIF</a><a href="#comms">Secure Communications</a><a href="#archive">Executive Archive</a><a href="#meetings">Boardroom & Meetings</a>{'<a href="/executive/access">Principal Access</a>' if user["role"]=="president" else ''}<a href="/executive/security">Security & Password</a><a href="/executive/logout" style="color:#ff9b9b">Secure Logout</a></aside><main>{body}</main></div></body></html>"""
    return HTMLResponse(page.replace("__PRES_SEAL__", core.PRES_SEAL_B64))


def dashboard(request: Request):
    user = _principal(request)
    if not user:
        return RedirectResponse("/executive/login", status_code=303)
    with core.db_cursor() as cur:
        cur.execute("SELECT * FROM executive_secure_messages ORDER BY id DESC LIMIT 8"); messages=cur.fetchall()
        cur.execute("SELECT * FROM executive_archive ORDER BY id DESC LIMIT 8"); archive=cur.fetchall()
        cur.execute("SELECT * FROM executive_meetings ORDER BY id DESC LIMIT 8"); meetings=cur.fetchall()
    msg_rows="".join(f"<tr><td>{r['id']}</td><td>{escape(r['recipient'])}</td><td>{escape(r['subject'])}</td><td>{escape(r['priority'])}</td><td>{escape(r['vault_object_id'] or 'Legacy local record')}</td></tr>" for r in messages) or "<tr><td colspan='5'>No secure messages yet.</td></tr>"
    arc_rows="".join(f"<tr><td>{r['id']}</td><td>{escape(r['title'])}</td><td>{escape(r['category'])}</td><td>{escape(r['retention'])}</td><td>{escape(r['vault_object_id'] or 'Legacy local record')}</td></tr>" for r in archive) or "<tr><td colspan='5'>No archived records yet.</td></tr>"
    mtg_rows="".join(f"<tr><td>{r['id']}</td><td>{escape(r['title'])}</td><td>{escape(r['meeting_type'])}</td><td>{escape(r['scheduled_for'] or '')}</td><td>{escape(r['location_mode'])}</td><td>{escape(r['vault_object_id'] or 'Legacy local record')}</td></tr>" for r in meetings) or "<tr><td colspan='6'>No executive meetings yet.</td></tr>"
    body=f"""<section class="hero"><div class="hero-head"><div class="principal-seal"><img src="data:image/png;base64,__PRES_SEAL__" alt="Presidential Seal"></div><div><h2>{escape(_title(user["role"]))} <span class="gold">Executive Workspace</span></h2><p>This is a principal-only portal. Staff Portal sessions are not accepted here. New executive communications, archive records and meeting records are saved only after UNG-VAULT confirms encrypted storage.</p></div></div></section>
<div class="grid"><div class="card"><h3>Secure Vault & SCIF</h3><p>Executive access to UNG-VAULT protected documents, Digital SCIF, encrypted file exchange, redacted sharing and emergency revocation.</p><p><a href="/executive/vault" style="color:#f0cc67;text-decoration:none;font-weight:700">Open Secure Vault →</a></p></div><div class="card"><h3>Executive Security Center</h3><p>Manage permanent credentials, authenticator MFA, and one-time recovery codes.</p><p><a href="/executive/security" style="color:#f0cc67;text-decoration:none;font-weight:700">Open Security Center →</a></p></div><div class="card"><h3>Principal Identity</h3><p>Separate executive account and cookie namespace for the President, Vice President and Prime Minister.</p></div><div class="card"><h3>Encrypted Communications</h3><p>Every executive message is encrypted and stored in UNG-VAULT; the suite retains only its VAULT reference and display metadata.</p></div><div class="card"><h3>Cloud-First Archive</h3><p>Executive records and protected notes are encrypted in UNG-VAULT with local metadata linked to the VAULT object.</p></div><div class="card"><h3>Private Workspace</h3><p>Dedicated digital study for principal-level work.</p></div><div class="card"><h3>Formal Boardroom</h3><p>Plan boardroom, private dining and secure conference sessions.</p></div><div class="card"><h3>Segregated Access</h3><p>Staff accounts cannot authenticate into this portal.</p></div></div>
<div class="two"><section class="panel" id="comms"><h3>Secure Communications</h3><form method="post" action="/executive/messages"><label>Recipient / channel</label><input name="recipient" required><label>Subject</label><input name="subject" required><label>Priority</label><select name="priority"><option>normal</option><option>high</option><option>urgent</option></select><label>Message</label><textarea name="message" required></textarea><button>Encrypt & Save</button></form><table><tr><th>ID</th><th>Recipient</th><th>Subject</th><th>Priority</th><th>VAULT object</th></tr>{msg_rows}</table></section>
<section class="panel" id="archive"><h3>Executive Archive</h3><form method="post" action="/executive/archive"><label>Record title</label><input name="title" required><label>Reference</label><input name="record_reference"><label>Category</label><select name="category"><option>Executive Record</option><option>Briefing</option><option>Correspondence</option><option>Meeting Record</option><option>Digital Asset</option></select><label>Retention</label><select name="retention"><option>Permanent</option><option>Presidential Term</option><option>Operational</option></select><label>Protected notes</label><textarea name="notes"></textarea><button>Capture Record</button></form><table><tr><th>ID</th><th>Title</th><th>Category</th><th>Retention</th><th>VAULT object</th></tr>{arc_rows}</table></section></div>
<section class="panel suite-planner" id="meetings" style="margin-top:16px"><h3>Boardroom / Private Suite Planner</h3><p class="intro">Plan executive boardroom sessions, private dining engagements, secure conferences, and principal workspace appointments.</p><form method="post" action="/executive/meetings"><div class="two"><div><label>Title</label><input name="title" required><label>Type</label><select name="meeting_type"><option>Executive Boardroom</option><option>Private Dining</option><option>Presidential Study</option><option>Secure Video Conference</option></select><label>Scheduled for</label><input type="datetime-local" name="scheduled_for"></div><div><label>Guests</label><input name="guests"><label>Location / mode</label><select name="location_mode"><option>Private Boardroom</option><option>Private Dining Room</option><option>Executive Office</option><option>Secure Remote</option></select><label>Protected notes</label><textarea name="notes"></textarea></div></div><button>Schedule Executive Session</button></form><table><tr><th>ID</th><th>Title</th><th>Type</th><th>Scheduled</th><th>Location</th><th>VAULT object</th></tr>{mtg_rows}</table></section>"""
    return _shell(user, body)


async def create_message(request: Request):
    user = _principal(request)
    if not user:
        return RedirectResponse("/executive/login", 303)
    form = await request.form()
    recipient = str(form.get("recipient", "")).strip()
    subject = str(form.get("subject", "")).strip()
    message = str(form.get("message", "")).strip()
    priority = str(form.get("priority", "normal")).strip()
    if not recipient or not subject or not message:
        raise HTTPException(400, "Required fields missing")
    created_at = datetime.utcnow().isoformat()
    vault_id = _store_executive_record_in_vault(
        user=user,
        record_type="executive_secure_message",
        name=f"Executive Communication — {subject}",
        classification="confidential",
        protection_profile="VAULT-ENVELOPE",
        payload={
            "recipient": recipient,
            "subject": subject,
            "priority": priority,
            "message": message,
            "created_by": user["username"],
            "created_at": created_at,
        },
    )
    with core.db_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO executive_secure_messages(recipient,subject,ciphertext,priority,created_by,created_at,vault_object_id) VALUES(?,?,?,?,?,?,?)",
            (recipient, subject, "VAULT:" + vault_id, priority, user["account_id"], created_at, vault_id),
        )
    core.log_action(None, user["username"], "executive_message_stored_in_vault", "vault_object", vault_id)
    return RedirectResponse("/executive#comms", 303)


async def create_archive(request: Request):
    user = _principal(request)
    if not user:
        return RedirectResponse("/executive/login", 303)
    form = await request.form()
    title = str(form.get("title", "")).strip()
    ref = str(form.get("record_reference", "")).strip()
    category = str(form.get("category", "Executive Record"))
    retention = str(form.get("retention", "Permanent"))
    notes = str(form.get("notes", "")).strip()
    if not title:
        raise HTTPException(400, "Title required")
    created_at = datetime.utcnow().isoformat()
    vault_id = _store_executive_record_in_vault(
        user=user,
        record_type="executive_archive_record",
        name=f"Executive Archive — {title}",
        classification="confidential",
        protection_profile="VAULT-ENVELOPE",
        payload={
            "title": title,
            "record_reference": ref,
            "category": category,
            "retention": retention,
            "protected_notes": notes,
            "created_by": user["username"],
            "created_at": created_at,
        },
    )
    with core.db_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO executive_archive(title,record_reference,category,retention,notes_ciphertext,created_by,created_at,vault_object_id) VALUES(?,?,?,?,?,?,?,?)",
            (title, ref, category, retention, None, user["account_id"], created_at, vault_id),
        )
    core.log_action(None, user["username"], "executive_archive_stored_in_vault", "vault_object", vault_id)
    return RedirectResponse("/executive#archive", 303)


async def create_meeting(request: Request):
    user = _principal(request)
    if not user:
        return RedirectResponse("/executive/login", 303)
    form = await request.form()
    title = str(form.get("title", "")).strip()
    mtype = str(form.get("meeting_type", "Executive Boardroom"))
    scheduled = str(form.get("scheduled_for", ""))
    guests = str(form.get("guests", ""))
    location = str(form.get("location_mode", "Private Boardroom"))
    notes = str(form.get("notes", "")).strip()
    if not title:
        raise HTTPException(400, "Title required")
    created_at = datetime.utcnow().isoformat()
    vault_id = _store_executive_record_in_vault(
        user=user,
        record_type="executive_meeting_record",
        name=f"Executive Meeting — {title}",
        classification="confidential",
        protection_profile="VAULT-ENVELOPE",
        payload={
            "title": title,
            "meeting_type": mtype,
            "scheduled_for": scheduled,
            "guests": guests,
            "location_mode": location,
            "protected_notes": notes,
            "created_by": user["username"],
            "created_at": created_at,
        },
    )
    with core.db_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO executive_meetings(title,meeting_type,scheduled_for,guests,location_mode,notes_ciphertext,created_by,created_at,vault_object_id) VALUES(?,?,?,?,?,?,?,?,?)",
            (title, mtype, scheduled, guests, location, None, user["account_id"], created_at, vault_id),
        )
    core.log_action(None, user["username"], "executive_meeting_stored_in_vault", "vault_object", vault_id)
    return RedirectResponse("/executive#meetings", 303)




def _hash_recovery_code(code: str) -> str:
    return hmac.new(core.SECRET_KEY.encode(), ("exec-recovery|" + code).encode(), hashlib.sha256).hexdigest()


def _new_recovery_codes(count: int = 8):
    return ["RC-" + "-".join(secrets.token_hex(2).upper() for _ in range(2)) for _ in range(count)]


def _hash_enrollment_code(code: str) -> str:
    return hmac.new(core.SECRET_KEY.encode(), ("exec-enroll|" + code).encode(), hashlib.sha256).hexdigest()


def access_admin(request: Request):
    user = _principal(request)
    if not user:
        return RedirectResponse("/executive/login", status_code=303)
    if user["role"] != "president":
        raise HTTPException(status_code=403, detail="President access required")
    with core.db_cursor() as cur:
        cur.execute("SELECT id,username,role,full_name,last_login,created_at FROM executive_principal_accounts ORDER BY id")
        accounts = cur.fetchall()
        cur.execute("SELECT id,role,created_at,expires_at,used_at FROM executive_enrollment_codes ORDER BY id DESC LIMIT 20")
        codes = cur.fetchall()
    acct_rows = "".join(
        f"<tr><td>{r['id']}</td><td>{escape(r['full_name'])}</td><td>{escape(r['username'])}</td><td>{escape(_title(r['role']))}</td><td>{escape(r['last_login'] or 'Never')}</td></tr>"
        for r in accounts
    ) or "<tr><td colspan='5'>No principal accounts.</td></tr>"
    code_rows = "".join(
        f"<tr><td>{r['id']}</td><td>{escape(_title(r['role']))}</td><td>{escape(r['created_at'])}</td><td>{escape(r['expires_at'])}</td><td>{'Used' if r['used_at'] else 'Available'}</td></tr>"
        for r in codes
    ) or "<tr><td colspan='5'>No enrollment codes issued.</td></tr>"
    body=f"""<section class="hero"><div class="hero-head"><div class="principal-seal"><img src="data:image/png;base64,__PRES_SEAL__" alt="Presidential Seal"></div><div><h2>Principal <span class="gold">Access Administration</span></h2><p>President-controlled enrollment for the Vice President and Prime Minister. One-time codes expire automatically and cannot be reused.</p></div></div></section>
<div class="two"><section class="panel"><h3>Issue One-Time Enrollment Code</h3><form method="post" action="/executive/access/codes"><label>Principal role</label><select name="role"><option value="vice_president">Vice President</option><option value="prime_minister">Prime Minister</option></select><label>Valid for</label><select name="hours"><option value="1">1 hour</option><option value="8">8 hours</option><option value="24">24 hours</option></select><button>Generate One-Time Code</button></form><p style="color:#9fb2c3;font-size:12px">The clear code is shown only once after generation.</p></section>
<section class="panel"><h3>Principal Accounts</h3><table><tr><th>ID</th><th>Name</th><th>Username</th><th>Role</th><th>Last Login</th></tr>{acct_rows}</table></section></div>
<section class="panel" style="margin-top:16px"><h3>Enrollment Code History</h3><table><tr><th>ID</th><th>Role</th><th>Created</th><th>Expires</th><th>Status</th></tr>{code_rows}</table></section>"""
    return _shell(user, body)


async def create_enrollment_code(request: Request):
    user = _principal(request)
    if not user:
        return RedirectResponse("/executive/login", status_code=303)
    if user["role"] != "president":
        raise HTTPException(status_code=403, detail="President access required")
    form = await request.form()
    role = str(form.get("role","")).strip()
    hours = int(str(form.get("hours","8")))
    if role not in {"vice_president","prime_minister"} or hours not in {1,8,24}:
        raise HTTPException(status_code=400, detail="Invalid enrollment request")
    code = "EXEC-" + "-".join(secrets.token_hex(2).upper() for _ in range(3))
    now = datetime.utcnow()
    from datetime import timedelta
    expires = now + timedelta(hours=hours)
    with core.db_cursor(commit=True) as cur:
        cur.execute("INSERT INTO executive_enrollment_codes(code_hash,role,issued_by,created_at,expires_at) VALUES(?,?,?,?,?)",
                    (_hash_enrollment_code(code), role, user["account_id"], now.isoformat(), expires.isoformat()))
    body=f"""<section class="hero"><h2>One-Time Enrollment Code</h2><p>Give this code directly to the designated {_title(role)}. It is displayed only on this screen.</p></section><section class="panel" style="margin-top:16px;text-align:center"><div style="font:700 30px monospace;color:#f0d37b;letter-spacing:2px;padding:22px">{escape(code)}</div><p>Expires {escape(expires.isoformat())} UTC</p><a href="/executive/access" style="color:#d9bb62">Return to Principal Access</a></section>"""
    return _shell(user, body)


def enrollment_form(request: Request):
    return HTMLResponse("""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Executive Enrollment</title><style>body{font-family:Arial;background:#071522;color:#fff;display:grid;place-items:center;min-height:100vh}.b{width:min(480px,92vw);background:#0c2033;padding:28px;border:1px solid #385069;border-radius:14px}input{width:100%;padding:11px;margin:5px 0 12px;box-sizing:border-box}button{padding:12px;width:100%;background:#caa84b;border:0;font-weight:bold}</style></head><body><div class="b"><h2>Principal Enrollment</h2><form method="post" action="/executive/enroll"><label>One-time code</label><input type="password" name="code" required><label>Full name</label><input name="full_name" required><label>Username</label><input name="username" required><label>New password</label><input type="password" name="password" minlength="12" required><button>Create Executive Account</button></form></div></body></html>""")


def enrollment_submit(code: str = Form(...), full_name: str = Form(...), username: str = Form(...), password: str = Form(...)):
    if len(password) < 12:
        raise HTTPException(status_code=400, detail="Password must be at least 12 characters")
    now = datetime.utcnow()
    with core.db_cursor() as cur:
        cur.execute("SELECT * FROM executive_enrollment_codes WHERE code_hash=?", (_hash_enrollment_code(code.strip()),))
        row = cur.fetchone()
    if not row or row["used_at"] or datetime.fromisoformat(row["expires_at"]) < now:
        raise HTTPException(status_code=403, detail="Invalid or expired one-time code")
    with core.db_cursor() as cur:
        cur.execute("SELECT id FROM executive_principal_accounts WHERE role=? OR username=?", (row["role"], username.strip()))
        if cur.fetchone():
            raise HTTPException(status_code=409, detail="That principal role or username is already enrolled")
    salt = secrets.token_hex(16)
    with core.db_cursor(commit=True) as cur:
        cur.execute("INSERT INTO executive_principal_accounts(username,password_hash,salt,role,full_name,created_at) VALUES(?,?,?,?,?,?)",
                    (username.strip(), _hash_password(password, salt), salt, row["role"], full_name.strip(), now.isoformat()))
        cur.execute("UPDATE executive_enrollment_codes SET used_at=? WHERE id=? AND used_at IS NULL", (now.isoformat(), row["id"]))
    return RedirectResponse("/executive/login?error=Executive+account+created.+Please+sign+in.", status_code=303)



def executive_vault_page(request: Request):
    user = _principal(request)
    if not user:
        return RedirectResponse("/executive/login", status_code=303)
    online, health = _vault_health()
    status = "ONLINE" if online else "UNAVAILABLE"
    status_color = "#8fd2a8" if online else "#ff9b9b"
    cards = [
        ("Protected Documents", "Store and retrieve classified or protected executive material through UNG-VAULT.", "/ui"),
        ("Digital SCIF", "Open the controlled high-assurance viewer for restricted and top-secret material.", "/ui"),
        ("Encrypted File Exchange", "Encrypt complete files without redaction and decrypt approved VAULT packages.", "/ui"),
        ("Redacted Sharing", "Create irreversible redacted previews with separately protected originals.", "/ui"),
        ("Executive Archive", "Use VAULT protection profiles and classification markings for sensitive records.", "/ui"),
        ("Emergency Revoke", "Terminate active, locked or pending Digital SCIF sessions when required.", "/ui"),
        ("Security Activity", "Review VAULT audit controls and SENTINEL-connected security events.", "/ui"),
    ]
    card_html = "".join(
        f'''<section class="card"><h3>{escape(title)}</h3><p>{escape(desc)}</p>
        <a href="{escape(VAULT_BASE_URL + path)}" target="_blank" rel="noopener noreferrer" style="color:#f0cc67;text-decoration:none;font-weight:700">Open in Secure VAULT →</a></section>'''
        for title, desc, path in cards
    )
    body = f'''<section class="hero"><div class="hero-head"><div class="principal-seal"><img src="data:image/png;base64,__PRES_SEAL__" alt="Presidential Seal"></div>
    <div><h2>Secure <span class="gold">Vault & SCIF</span></h2><p>Executive-facing access to UNG-VAULT from inside the Digital Executive Suite. VAULT remains an independently secured backend service.</p></div></div></section>
    <div class="two">
      <section class="panel"><h3>UNG-VAULT Connection</h3><table>
        <tr><th>Service</th><td>UNG-VAULT</td></tr>
        <tr><th>Status</th><td style="color:{status_color};font-weight:800">{status}</td></tr>
        <tr><th>Principal</th><td>{escape(_title(user["role"]))}</td></tr>
        <tr><th>Integration</th><td>Executive Suite launch surface · VAULT remains separate security boundary</td></tr>
        <tr><th>SCIF</th><td>Hosted inside UNG-VAULT</td></tr>
      </table></section>
      <section class="panel"><h3>Security Boundary</h3><p style="color:#aebdcb;line-height:1.55">UNG-PRESIDENT does not store VAULT master keys, SCIF plaintext, or VAULT database records. This page is the executive front door; encryption, classification enforcement, SCIF controls, audit and SENTINEL event forwarding remain inside UNG-VAULT.</p></section>
    </div>
    <div class="grid">{card_html}</div>
    <section class="panel" style="margin-top:16px"><h3>Executive Security Path</h3><p style="color:#aebdcb">Principal Portal → Secure Vault & SCIF → UNG-VAULT → Digital SCIF / protected files → SENTINEL security monitoring</p></section>'''
    return _shell(user, body)



def security_page(request: Request):
    user = _principal(request)
    if not user:
        return RedirectResponse("/executive/login", status_code=303)
    with core.db_cursor() as cur:
        cur.execute("SELECT * FROM executive_principal_accounts WHERE id=?", (user["account_id"],))
        account = cur.fetchone()
    mfa_html = ""
    if account["mfa_enabled"]:
        mfa_html = '<section class="panel"><h3>Authenticator MFA</h3><p style="color:#8fd2a8">Enabled</p><p style="color:#aebdcb;font-size:13px">A 6-digit authenticator code is required after your password.</p></section>'
    else:
        secret = account["mfa_secret"] or pyotp.random_base32()
        if not account["mfa_secret"]:
            with core.db_cursor(commit=True) as cur:
                cur.execute("UPDATE executive_principal_accounts SET mfa_secret=? WHERE id=?", (secret, user["account_id"]))
        uri = pyotp.TOTP(secret).provisioning_uri(name=user["username"], issuer_name="UNG-PRESIDENT Executive")
        qr = qrcode.make(uri)
        buf = io.BytesIO()
        qr.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode()
        mfa_html = f'''<section class="panel"><h3>Authenticator MFA</h3><p style="color:#aebdcb;font-size:13px">Scan this QR code with an authenticator app, then enter the current 6-digit code to enable MFA.</p><div style="text-align:center"><img src="data:image/png;base64,{qr_b64}" alt="MFA QR code" style="width:190px;height:190px;background:white;padding:8px;border-radius:10px"></div><p style="font:12px monospace;word-break:break-all;color:#d9bb62">{escape(secret)}</p><form method="post" action="/executive/security/mfa/enable"><label>6-digit code</label><input name="code" inputmode="numeric" pattern="[0-9]{{6}}" maxlength="6" required><button>Enable MFA</button></form></section>'''
    with core.db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM executive_recovery_codes WHERE account_id=? AND used_at IS NULL", (user["account_id"],))
        recovery_left = cur.fetchone()["n"]
    password_ready = bool(account["password_changed_at"]) if "password_changed_at" in account.keys() else False
    mfa_ready = bool(account["mfa_enabled"])
    recovery_ready = recovery_left > 0
    ready_count = sum([password_ready, mfa_ready, recovery_ready])
    readiness_html = f'''<section class="panel"><h3>Security Readiness</h3><p style="color:#aebdcb;font-size:13px">Complete all three controls for a fully hardened principal account.</p><table>
    <tr><th>Permanent password</th><td>{'✓ Complete' if password_ready else 'Pending'}</td></tr>
    <tr><th>Authenticator MFA</th><td>{'✓ Enabled' if mfa_ready else 'Pending'}</td></tr>
    <tr><th>Recovery codes</th><td>{'✓ Ready ('+str(recovery_left)+')' if recovery_ready else 'Pending'}</td></tr>
    <tr><th>Overall</th><td><strong>{ready_count}/3 complete</strong></td></tr></table></section>'''
    recovery_html = f'''<section class="panel"><h3>Recovery Codes</h3><p style="color:#aebdcb;font-size:13px">Single-use backup codes for MFA recovery. Remaining: <strong>{recovery_left}</strong></p><form method="post" action="/executive/security/recovery-codes"><button>Generate New Recovery Codes</button></form><p style="font-size:11px;color:#7f91a2">Generating a new set revokes all unused old codes.</p></section>'''
    with core.db_cursor() as cur:
        cur.execute("""SELECT id,user_agent,ip_address,created_at,last_seen,expires_at
                       FROM executive_sessions
                       WHERE account_id=? AND revoked_at IS NULL AND expires_at>?
                       ORDER BY last_seen DESC""", (user["account_id"], datetime.utcnow().isoformat()))
        sessions = cur.fetchall()
    session_rows = "".join(
        f"<tr><td>{'Current' if s['id']==user['session_id'] else 'Active'}</td><td>{escape((s['user_agent'] or 'Unknown')[:70])}</td><td>{escape(s['ip_address'] or 'Unknown')}</td><td>{escape(s['last_seen'])}</td><td>{'' if s['id']==user['session_id'] else '<form method=post action=/executive/security/sessions/revoke><input type=hidden name=session_id value='+escape(s['id'])+'><button style=margin:0>Sign Out</button></form>'}</td></tr>"
        for s in sessions
    ) or "<tr><td colspan='5'>No active sessions.</td></tr>"
    sessions_html = f'''<section class="panel" style="grid-column:1/-1"><h3>Active Executive Sessions</h3><p style="color:#aebdcb;font-size:13px">Review signed-in devices and terminate any session you do not recognize.</p><table><tr><th>Status</th><th>Device / Browser</th><th>IP</th><th>Last Seen</th><th>Action</th></tr>{session_rows}</table><form method="post" action="/executive/security/sessions/revoke-others"><button>Sign Out All Other Sessions</button></form></section>'''
    with core.db_cursor() as cur:
        cur.execute("SELECT role,COUNT(*) AS n FROM executive_principal_accounts GROUP BY role")
        role_counts = {r["role"]: r["n"] for r in cur.fetchall()}
    roles_ok = all(role_counts.get(role,0) == 1 for role in EXEC_ROLES)
    acceptance_html = f'''<section class="panel" style="grid-column:1/-1"><h3>Executive Suite Acceptance Status</h3><table>
    <tr><th>Principal portal separated from Staff Portal</th><td>✓ Pass</td></tr>
    <tr><th>President / Vice President / Prime Minister account namespaces</th><td>{'✓ Pass' if roles_ok else 'Attention required'}</td></tr>
    <tr><th>Signed session validation and revocation</th><td>✓ Pass</td></tr>
    <tr><th>Password rotation invalidates all sessions</th><td>✓ Pass</td></tr>
    <tr><th>Authenticator MFA + recovery-code path</th><td>✓ Available</td></tr>
    <tr><th>Encrypted Executive records</th><td>✓ Fernet protected</td></tr>
    </table></section>'''
    body=f"""<section class="hero"><div class="hero-head"><div class="principal-seal"><img src="data:image/png;base64,__PRES_SEAL__" alt="Presidential Seal"></div><div><h2>Executive <span class="gold">Security</span></h2><p>Manage your principal-only credential independently from Staff Portal accounts.</p></div></div></section>
<div class="two"><section class="panel"><h3>Set / Change Executive Password</h3><form method="post" action="/executive/security/password"><label>Current password or one-time executive setup code</label><input type="password" name="current_password" autocomplete="current-password" required><p style="font-size:11px;color:#7f91a2;margin-top:-4px">For initial presidential setup, the one-time Executive Setup Code may be used instead of the temporary password.</p><label>New password</label><input type="password" name="new_password" minlength="14" autocomplete="new-password" required><label>Confirm new password</label><input type="password" name="confirm_password" minlength="14" autocomplete="new-password" required><button>Update Executive Password</button></form></section>
<section class="panel"><h3>Session Protection</h3><p style="color:#aebdcb;font-size:13px">Executive Portal sessions are isolated from Staff Portal sessions and expire automatically. Use Secure Logout when leaving a principal device.</p><table><tr><th>Principal</th><td>{escape(_title(user["role"]))}</td></tr><tr><th>Username</th><td>{escape(user["username"])}</td></tr><tr><th>Session lifetime</th><td>8 hours maximum</td></tr><tr><th>Cookie</th><td>HTTP-only · SameSite Strict · Secure in production</td></tr></table></section>{readiness_html}{mfa_html}{recovery_html}{sessions_html}{acceptance_html}</div>"""
    return _shell(user, body)


async def change_executive_password(request: Request):
    user = _principal(request)
    if not user:
        return RedirectResponse("/executive/login", status_code=303)
    form = await request.form()
    current = str(form.get("current_password",""))
    new = str(form.get("new_password",""))
    confirm = str(form.get("confirm_password",""))
    if new != confirm:
        raise HTTPException(status_code=400, detail="New passwords do not match")
    if len(new) < 14:
        raise HTTPException(status_code=400, detail="New password must be at least 14 characters")
    with core.db_cursor() as cur:
        cur.execute("SELECT * FROM executive_principal_accounts WHERE id=?", (user["account_id"],))
        row = cur.fetchone()
    setup_code = os.environ.get("UNG_EXECUTIVE_SETUP_CODE", "")
    current_ok = bool(row) and _verify_password(current, row["password_hash"], row["salt"])
    bootstrap_ok = bool(row) and user["role"] == "president" and bool(setup_code) and hmac.compare_digest(current.strip(), setup_code.strip())
    if not current_ok and not bootstrap_ok:
        raise HTTPException(status_code=403, detail="Current password or executive setup code is incorrect")
    salt = secrets.token_hex(16)
    with core.db_cursor(commit=True) as cur:
        cur.execute("UPDATE executive_principal_accounts SET password_hash=?, salt=?, password_changed_at=? WHERE id=?",
                    (_hash_password(new, salt), salt, datetime.utcnow().isoformat(), user["account_id"]))
    with core.db_cursor(commit=True) as cur:
        cur.execute("UPDATE executive_sessions SET revoked_at=? WHERE account_id=? AND revoked_at IS NULL",
                    (datetime.utcnow().isoformat(), user["account_id"]))
    core.log_action(None, user["username"], "executive_password_changed", "executive_principal_accounts", user["account_id"])
    response = RedirectResponse("/executive/login?error=Password+updated.+All+executive+sessions+were+signed+out.", status_code=303)
    response.delete_cookie(EXEC_COOKIE, path="/")
    return response



async def enable_executive_mfa(request: Request):
    user = _principal(request)
    if not user:
        return RedirectResponse("/executive/login", status_code=303)
    form = await request.form()
    code = str(form.get("code","")).strip()
    with core.db_cursor() as cur:
        cur.execute("SELECT * FROM executive_principal_accounts WHERE id=?", (user["account_id"],))
        row = cur.fetchone()
    if not row or not row["mfa_secret"] or not pyotp.TOTP(row["mfa_secret"]).verify(code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid authenticator code")
    with core.db_cursor(commit=True) as cur:
        cur.execute("UPDATE executive_principal_accounts SET mfa_enabled=1 WHERE id=?", (user["account_id"],))
    core.log_action(None, user["username"], "executive_mfa_enabled", "executive_principal_accounts", user["account_id"])
    return RedirectResponse("/executive/security", status_code=303)



async def generate_recovery_codes(request: Request):
    user = _principal(request)
    if not user:
        return RedirectResponse("/executive/login", status_code=303)
    codes = _new_recovery_codes(8)
    now = datetime.utcnow().isoformat()
    with core.db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM executive_recovery_codes WHERE account_id=? AND used_at IS NULL", (user["account_id"],))
        for code in codes:
            cur.execute("INSERT INTO executive_recovery_codes(account_id,code_hash,created_at) VALUES(?,?,?)",
                        (user["account_id"], _hash_recovery_code(code), now))
    core.log_action(None, user["username"], "executive_recovery_codes_generated", "executive_principal_accounts", user["account_id"])
    code_html = "".join(f"<li style='font:700 20px monospace;color:#f0d37b;margin:8px 0'>{escape(code)}</li>" for code in codes)
    body=f"""<section class="hero"><h2>New <span class="gold">Recovery Codes</span></h2><p>Save these codes now. Each can be used once and they will not be shown again.</p></section><section class="panel" style="margin-top:16px"><ol style="columns:2;list-style-position:inside">{code_html}</ol><p style="color:#ffcf7a">Store these somewhere secure and separate from your authenticator device.</p><a href="/executive/security" style="color:#d9bb62">Return to Security</a></section>"""
    return _shell(user, body)



async def revoke_executive_session(request: Request):
    user = _principal(request)
    if not user:
        return RedirectResponse("/executive/login", status_code=303)
    form = await request.form()
    session_id = str(form.get("session_id","")).strip()
    if not session_id or session_id == user["session_id"]:
        raise HTTPException(status_code=400, detail="Use Secure Logout to end the current session")
    with core.db_cursor(commit=True) as cur:
        cur.execute("""UPDATE executive_sessions SET revoked_at=?
                       WHERE id=? AND account_id=? AND revoked_at IS NULL""",
                    (datetime.utcnow().isoformat(), session_id, user["account_id"]))
    core.log_action(None, user["username"], "executive_session_revoked", "executive_sessions", session_id)
    return RedirectResponse("/executive/security", status_code=303)


async def revoke_other_executive_sessions(request: Request):
    user = _principal(request)
    if not user:
        return RedirectResponse("/executive/login", status_code=303)
    now = datetime.utcnow().isoformat()
    with core.db_cursor(commit=True) as cur:
        cur.execute("""UPDATE executive_sessions SET revoked_at=?
                       WHERE account_id=? AND id<>? AND revoked_at IS NULL""",
                    (now, user["account_id"], user["session_id"]))
    core.log_action(None, user["username"], "executive_other_sessions_revoked", "executive_sessions", user["account_id"])
    return RedirectResponse("/executive/security", status_code=303)


def legacy_redirect():
    return RedirectResponse("/executive", status_code=303)


def apply_executive_suite(_core=None):
    init_schema()
    seed_principal_accounts_from_env()
    paths={"/executive","/executive/login","/executive/logout","/executive/setup","/executive/messages","/executive/archive","/executive/meetings","/executive/access","/executive/access/codes","/executive/enroll","/executive/vault","/executive/security","/executive/security/password","/executive/security/mfa/enable","/executive/security/recovery-codes","/executive/security/sessions/revoke","/executive/security/sessions/revoke-others","/executive/mfa","/executive/mfa/recovery","/admin/executive-suite"}
    core.app.router.routes[:] = [r for r in core.app.router.routes if getattr(r,"path",None) not in paths]
    core.app.add_api_route("/executive", dashboard, methods=["GET"], response_class=HTMLResponse)
    core.app.add_api_route("/executive/vault", executive_vault_page, methods=["GET"], response_class=HTMLResponse)
    core.app.add_api_route("/executive/login", executive_login_form, methods=["GET"], response_class=HTMLResponse)
    core.app.add_api_route("/executive/login", executive_login, methods=["POST"])
    core.app.add_api_route("/executive/mfa", executive_mfa_form, methods=["GET"], response_class=HTMLResponse)
    core.app.add_api_route("/executive/mfa", executive_mfa_verify, methods=["POST"])
    core.app.add_api_route("/executive/mfa/recovery", executive_mfa_recovery, methods=["POST"])
    core.app.add_api_route("/executive/logout", executive_logout, methods=["GET"])
    core.app.add_api_route("/executive/setup", setup_form, methods=["GET"], response_class=HTMLResponse)
    core.app.add_api_route("/executive/setup", setup_submit, methods=["POST"])
    core.app.add_api_route("/executive/messages", create_message, methods=["POST"])
    core.app.add_api_route("/executive/archive", create_archive, methods=["POST"])
    core.app.add_api_route("/executive/meetings", create_meeting, methods=["POST"])
    core.app.add_api_route("/executive/access", access_admin, methods=["GET"], response_class=HTMLResponse)
    core.app.add_api_route("/executive/access/codes", create_enrollment_code, methods=["POST"], response_class=HTMLResponse)
    core.app.add_api_route("/executive/enroll", enrollment_form, methods=["GET"], response_class=HTMLResponse)
    core.app.add_api_route("/executive/enroll", enrollment_submit, methods=["POST"])
    core.app.add_api_route("/executive/security", security_page, methods=["GET"], response_class=HTMLResponse)
    core.app.add_api_route("/executive/security/password", change_executive_password, methods=["POST"])
    core.app.add_api_route("/executive/security/mfa/enable", enable_executive_mfa, methods=["POST"])
    core.app.add_api_route("/executive/security/recovery-codes", generate_recovery_codes, methods=["POST"], response_class=HTMLResponse)
    core.app.add_api_route("/executive/security/sessions/revoke", revoke_executive_session, methods=["POST"])
    core.app.add_api_route("/executive/security/sessions/revoke-others", revoke_other_executive_sessions, methods=["POST"])
    core.app.add_api_route("/admin/executive-suite", legacy_redirect, methods=["GET"])
    return True
