"""Production password-recovery extension for UNG-PRESIDENT.

Keeps recovery data separate from the core users table, uses the existing
staff_profiles.personal_email field, stores only reset-token hashes, and
invalidates sessions issued before a successful password change.
"""
import hashlib
import hmac
import os
import secrets
import smtplib
import time
from datetime import datetime, timedelta
from email.message import EmailMessage

import uvicorn
from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

import ung_president as core

RESET_TOKEN_MAX_AGE_SECONDS = 20 * 60

RESET_REQUEST = """
{% extends "base" %}{% block title %}Reset Staff Password{% endblock %}
{% block content %}<div class="container" style="max-width:620px;">
<h2 class="section-title">Reset Staff Password</h2>
{% if message %}<div class="alert alert-success">{{ message }}</div>{% endif %}
<form class="stack" method="post" action="/admin/password-reset">
<label>Username</label><input type="text" name="username" required autocomplete="username">
<label>Personal Email</label><input type="email" name="personal_email" required autocomplete="email">
<button class="btn btn-gold" type="submit">Continue</button></form>
<p class="hint">If the information matches a staff account, reset instructions will be sent to the registered recovery email.</p>
<p><a href="/admin/login">&larr; Back to Staff Login</a></p></div>{% endblock %}
"""
RESET_COMPLETE = """
{% extends "base" %}{% block title %}Choose New Password{% endblock %}
{% block content %}<div class="container" style="max-width:620px;">
<h2 class="section-title">Choose New Password</h2>
{% if error %}<div class="alert alert-error">{{ error }}</div>{% endif %}
<form class="stack" method="post" action="/admin/password-reset/complete">
<input type="hidden" name="token" value="{{ token }}">
<label>New Password</label><input type="password" name="password" required minlength="12" autocomplete="new-password">
<label>Confirm New Password</label><input type="password" name="confirm_password" required minlength="12" autocomplete="new-password">
<p class="hint">Minimum 12 characters with uppercase, lowercase, a number, and a special character.</p>
<button class="btn btn-gold" type="submit">Reset Password</button></form></div>{% endblock %}
"""


def _ensure_schema():
    # The extension may be the process entrypoint on a brand-new Railway
    # filesystem. Create the core tables before extending the users schema.
    core.init_db()
    with core.db_cursor(commit=True) as cur:
        cur.execute("""CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            used_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )""")
        cols = {r[1] for r in cur.execute("PRAGMA table_info(users)").fetchall()}
        if "password_changed_at" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN password_changed_at TEXT")


def _token_hash(token: str) -> str:
    return hashlib.sha256((token + ":" + core.SECRET_KEY).encode()).hexdigest()


def create_password_reset_token(username: str, personal_email: str):
    """Return a reset token only when username + registered recovery email match."""
    _ensure_schema()
    with core.db_cursor() as cur:
        cur.execute("""SELECT u.id FROM users u JOIN staff_profiles s ON s.user_id=u.id
                       WHERE u.username=? AND lower(s.personal_email)=lower(?)""",
                    (username.strip(), personal_email.strip()))
        row = cur.fetchone()
    if not row:
        return None
    token = secrets.token_urlsafe(32)
    expires = (datetime.utcnow() + timedelta(seconds=RESET_TOKEN_MAX_AGE_SECONDS)).isoformat()
    with core.db_cursor(commit=True) as cur:
        cur.execute("UPDATE password_reset_tokens SET used_at=? WHERE user_id=? AND used_at IS NULL",
                    (datetime.utcnow().isoformat(), row["id"]))
        cur.execute("INSERT INTO password_reset_tokens(user_id,token_hash,expires_at) VALUES(?,?,?)",
                    (row["id"], _token_hash(token), expires))
    return token


def _send_reset_email(to_email: str, token: str) -> bool:
    host = os.environ.get("UNG_PRESIDENT_SMTP_HOST")
    sender = os.environ.get("UNG_PRESIDENT_RESET_FROM")
    public_url = os.environ.get("UNG_PRESIDENT_PUBLIC_URL", "").rstrip("/")
    if not (host and sender and public_url):
        return False
    msg = EmailMessage()
    msg["Subject"] = "UNG-PRESIDENT staff password reset"
    msg["From"] = sender
    msg["To"] = to_email
    msg.set_content(f"Use this link within 20 minutes to reset your staff password:\n{public_url}/admin/password-reset/complete?token={token}\n\nIf you did not request this, ignore this message.")
    port = int(os.environ.get("UNG_PRESIDENT_SMTP_PORT", "587"))
    user = os.environ.get("UNG_PRESIDENT_SMTP_USER")
    password = os.environ.get("UNG_PRESIDENT_SMTP_PASSWORD")
    with smtplib.SMTP(host, port, timeout=10) as smtp:
        smtp.starttls()
        if user:
            smtp.login(user, password or "")
        smtp.send_message(msg)
    return True


def _verify_session_with_password_epoch(token: str):
    try:
        raw = core.base64.urlsafe_b64decode(token.encode()).decode()
        user_id, username, role, issued, sig = raw.split("|")
        payload = f"{user_id}|{username}|{role}|{issued}"
        expected = hmac.new(core.SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected) or int(time.time()) - int(issued) > core.SESSION_MAX_AGE_SECONDS:
            return None
        with core.db_cursor() as cur:
            cur.execute("SELECT password_changed_at FROM users WHERE id=?", (int(user_id),))
            row = cur.fetchone()
        if not row:
            return None
        changed = row["password_changed_at"]
        if changed and int(issued) <= int(datetime.fromisoformat(changed).timestamp()):
            return None
        return {"user_id": int(user_id), "username": username, "role": role}
    except Exception:
        return None


def install():
    _ensure_schema()
    core.verify_session_token = _verify_session_with_password_epoch
    core.env.loader.mapping["password_reset"] = RESET_REQUEST
    core.env.loader.mapping["password_reset_complete"] = RESET_COMPLETE
    login = core.env.loader.mapping["login"]
    if '/admin/password-reset' not in login:
        login = login.replace('</form>', '</form><p style="text-align:center;"><a href="/admin/password-reset">Forgot password?</a></p>', 1)
        core.env.loader.mapping["login"] = login

    @core.app.get("/admin/password-reset", response_class=HTMLResponse)
    def reset_form(message: str = ""):
        return core.render("password_reset", message=message)

    @core.app.post("/admin/password-reset")
    def reset_request(request: Request, username: str = Form(...), personal_email: str = Form(...)):
        generic = "If the information matches a staff account, reset instructions have been sent."
        if core.is_rate_limited(f"password-reset:{core.client_ip(request)}", 5, 900):
            return core.render("password_reset", message=generic)
        token = create_password_reset_token(username, personal_email)
        if token:
            try:
                _send_reset_email(personal_email.strip(), token)
            except Exception:
                pass
            core.log_action(None, username, "password_reset_requested", "users", detail="recovery request", ip_address=core.client_ip(request))
        else:
            core.log_action(None, None, "password_reset_requested", detail="generic recovery request", ip_address=core.client_ip(request))
        return core.render("password_reset", message=generic)

    @core.app.get("/admin/password-reset/complete", response_class=HTMLResponse)
    def reset_complete_form(token: str):
        return core.render("password_reset_complete", token=token, error="")

    @core.app.post("/admin/password-reset/complete")
    def reset_complete(request: Request, token: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
        def fail(msg):
            return HTMLResponse(core.render("password_reset_complete", token=token, error=msg), status_code=400)
        if password != confirm_password:
            return fail("Passwords do not match.")
        ok, reason = core.password_meets_policy(password)
        if not ok:
            return fail(reason)
        now = datetime.utcnow()
        with core.db_cursor() as cur:
            cur.execute("SELECT * FROM password_reset_tokens WHERE token_hash=?", (_token_hash(token),))
            row = cur.fetchone()
        if not row or row["used_at"] or datetime.fromisoformat(row["expires_at"]) < now:
            return fail("This reset link is invalid or has expired.")
        pw_hash, salt = core.hash_password(password)
        changed_at = now.isoformat()
        with core.db_cursor(commit=True) as cur:
            cur.execute("UPDATE users SET password_hash=?,salt=?,failed_attempts=0,locked_until=NULL,password_changed_at=? WHERE id=?",
                        (pw_hash, salt, changed_at, row["user_id"]))
            cur.execute("UPDATE password_reset_tokens SET used_at=? WHERE id=? AND used_at IS NULL", (changed_at, row["id"]))
            if cur.rowcount != 1:
                return fail("This reset link is invalid or has expired.")
            cur.execute("SELECT username FROM users WHERE id=?", (row["user_id"],))
            user = cur.fetchone()
        core.log_action(row["user_id"], user["username"], "password_reset_completed", "users", row["user_id"], detail="sessions invalidated", ip_address=core.client_ip(request))
        response = RedirectResponse("/admin/login?error=Password+reset+complete.+Please+sign+in.", status_code=303)
        response.delete_cookie("session")
        return response

install()
app = core.app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
