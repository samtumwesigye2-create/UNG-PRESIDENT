"""Separate principal-only Digital Executive Suite for UNG-PRESIDENT."""
import base64
import hashlib
import hmac
import os
import secrets
import time
from datetime import datetime
from html import escape

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

import ung_president as core

EXEC_COOKIE = "executive_session"
EXEC_MAX_AGE = 60 * 60 * 8
EXEC_ROLES = {"president", "vice_president", "prime_minister"}


def _fernet():
    key = base64.urlsafe_b64encode(hashlib.sha256((core.SECRET_KEY + "|executive-suite").encode()).digest())
    return Fernet(key)


def _hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), core.PBKDF2_ITERATIONS)
    return base64.b64encode(digest).decode()


def _verify_password(password: str, stored_hash: str, salt: str) -> bool:
    return hmac.compare_digest(_hash_password(password, salt), stored_hash)


def _token(account_id: int, username: str, role: str) -> str:
    issued = int(time.time())
    payload = f"executive|{account_id}|{username}|{role}|{issued}"
    sig = hmac.new(core.SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}|{sig}".encode()).decode()


def _verify_token(token: str):
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        purpose, account_id, username, role, issued, sig = raw.split("|")
        if purpose != "executive" or role not in EXEC_ROLES:
            return None
        payload = f"{purpose}|{account_id}|{username}|{role}|{issued}"
        expected = hmac.new(core.SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        if int(time.time()) - int(issued) > EXEC_MAX_AGE:
            return None
        return {"account_id": int(account_id), "username": username, "role": role}
    except Exception:
        return None


def _principal(request: Request):
    token = request.cookies.get(EXEC_COOKIE)
    user = _verify_token(token) if token else None
    if not user:
        return None
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
            last_login TEXT
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS executive_secure_messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            ciphertext TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'normal',
            created_by INTEGER,
            created_at TEXT NOT NULL
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS executive_archive(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            record_reference TEXT,
            category TEXT NOT NULL,
            retention TEXT NOT NULL,
            notes_ciphertext TEXT,
            created_by INTEGER,
            created_at TEXT NOT NULL
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
            created_at TEXT NOT NULL
        )""")


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
</style></head><body><div class="box"><div class="crest"><img src="data:image/png;base64,{{PRES_SEAL}}" alt="Presidential Seal"></div><h1>Digital Executive Suite</h1><div class="sub">PRINCIPAL ACCESS · REPUBLIC OF UGANDA</div>{err}
<form method="post" action="/executive/login"><label>Executive username</label><input name="username" autocomplete="username" required><label>Password</label><input type="password" name="password" autocomplete="current-password" required><button>Enter Executive Portal</button></form>
<div class="note">President · Vice President · Prime Minister only</div></div></body></html>"""
    page = page.replace("{{PRES_SEAL}}", core.PRES_SEAL_B64)
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
    with core.db_cursor(commit=True) as cur:
        cur.execute("UPDATE executive_principal_accounts SET last_login=? WHERE id=?", (datetime.utcnow().isoformat(), row["id"]))
    core.log_action(None, row["username"], "executive_portal_login", "executive_principal_accounts", row["id"])
    response = RedirectResponse("/executive", status_code=303)
    response.set_cookie(EXEC_COOKIE, _token(row["id"], row["username"], row["role"]), httponly=True, samesite="strict", secure=bool(os.environ.get("RAILWAY_ENVIRONMENT_ID")), max_age=EXEC_MAX_AGE, path="/")
    return response


def executive_logout():
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
<style>body{font-family:Arial;background:#071522;color:#fff;display:grid;place-items:center;min-height:100vh}.b{width:min(480px,92vw);background:#0c2033;padding:28px;border:1px solid #385069;border-radius:14px}input,select{width:100%;padding:11px;margin:5px 0 12px;box-sizing:border-box}button{padding:12px;width:100%;background:#caa84b;border:0;font-weight:bold}</style></head><body><div class="b"><h2>Initial Executive Principal Enrollment</h2><form method="post" action="/executive/setup"><label>Setup code</label><input type="password" name="setup_code" required><label>Full name</label><input name="full_name" required><label>Username</label><input name="username" required><label>Role</label><select name="role"><option value="president">President</option><option value="vice_president">Vice President</option><option value="prime_minister">Prime Minister</option></select><label>Password</label><input type="password" name="password" minlength="12" required><button>Create Principal Account</button></form></div></body></html>""")


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
    return HTMLResponse(f"""<!doctype html><html><head><meta name="viewport" content="width=1180,initial-scale=1"><title>{escape(_title(user["role"]))} Executive Suite</title>
<style>
*{{box-sizing:border-box}}html,body{{margin:0;min-width:1180px;background:#07111f;color:#edf2f7;font-family:Arial,sans-serif}}body{{overflow-x:auto}}
.top{{height:104px;background:linear-gradient(90deg,#061529,#0b2948);border-bottom:2px solid #caa447;display:flex;align-items:center;justify-content:space-between;padding:0 34px}}.brand h1{{font:29px Georgia;margin:0}}.brand small{{color:#d7b85c;letter-spacing:2px}}.who{{text-align:right;color:#aebdcb;font-size:12px}}
.layout{{display:grid;grid-template-columns:250px 1fr;min-height:calc(100vh - 104px)}}aside{{background:#081827;border-right:1px solid #20364d;padding:28px 20px}}aside a{{display:block;color:#dfe8f1;text-decoration:none;padding:11px 12px;border-radius:7px;margin-bottom:5px}}aside a:hover{{background:#102b47;color:#f2cf69}}
main{{padding:32px 34px;max-width:1450px}}.hero{{background:linear-gradient(120deg,#0e2d4c,#102039);border:1px solid #2a435d;border-radius:16px;padding:30px}}.hero h2{{font:31px Georgia;margin:0 0 8px}}.gold{{color:#d6b354}}.hero p{{color:#b8c7d6}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:18px}}.card,.panel{{background:#0c1d2e;border:1px solid #233b53;border-radius:13px;padding:19px}}.card h3{{color:#f0cc67;margin-top:0}}.card p{{color:#aebdcb;font-size:13px;line-height:1.45}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:18px}}label{{display:block;font-size:12px;font-weight:700;margin:10px 0 5px;color:#c9d3dd}}input,textarea,select{{width:100%;background:#07131f;color:#eef3f8;border:1px solid #334a61;border-radius:7px;padding:10px}}textarea{{min-height:88px}}button{{margin-top:12px;background:#c7a247;color:#07111f;border:0;border-radius:7px;padding:10px 14px;font-weight:800}}table{{width:100%;border-collapse:collapse;margin-top:12px;font-size:12px}}th,td{{padding:9px;border-bottom:1px solid #24384b;text-align:left;vertical-align:top}}th{{color:#d9ba61}}
</style></head><body><div class="top"><div class="brand"><h1>DIGITAL EXECUTIVE SUITE</h1><small>PRINCIPAL PORTAL · UNG-PRESIDENT</small></div><div class="who">{escape(_title(user["role"]).upper())}<br><strong>{escape(user["username"])}</strong></div></div>
<div class="layout"><aside><a href="/executive">Executive Home</a><a href="#comms">Secure Communications</a><a href="#archive">Executive Archive</a><a href="#meetings">Boardroom & Meetings</a><a href="/executive/logout" style="color:#ff9b9b">Secure Logout</a></aside><main>{body}</main></div></body></html>""")


def dashboard(request: Request):
    user = _principal(request)
    if not user:
        return RedirectResponse("/executive/login", status_code=303)
    f = _fernet()
    with core.db_cursor() as cur:
        cur.execute("SELECT * FROM executive_secure_messages ORDER BY id DESC LIMIT 8"); messages=cur.fetchall()
        cur.execute("SELECT * FROM executive_archive ORDER BY id DESC LIMIT 8"); archive=cur.fetchall()
        cur.execute("SELECT * FROM executive_meetings ORDER BY id DESC LIMIT 8"); meetings=cur.fetchall()
    msg_rows="".join(f"<tr><td>{r['id']}</td><td>{escape(r['recipient'])}</td><td>{escape(r['subject'])}</td><td>{escape(r['priority'])}</td><td>{escape(_decrypt(r['ciphertext'])[:120])}</td></tr>" for r in messages) or "<tr><td colspan='5'>No secure messages yet.</td></tr>"
    arc_rows="".join(f"<tr><td>{r['id']}</td><td>{escape(r['title'])}</td><td>{escape(r['category'])}</td><td>{escape(r['retention'])}</td></tr>" for r in archive) or "<tr><td colspan='4'>No archived records yet.</td></tr>"
    mtg_rows="".join(f"<tr><td>{r['id']}</td><td>{escape(r['title'])}</td><td>{escape(r['meeting_type'])}</td><td>{escape(r['scheduled_for'] or '')}</td><td>{escape(r['location_mode'])}</td></tr>" for r in meetings) or "<tr><td colspan='5'>No executive meetings yet.</td></tr>"
    body=f"""<section class="hero"><h2>{escape(_title(user["role"]))} <span class="gold">Executive Workspace</span></h2><p>This is a principal-only portal. Staff Portal sessions are not accepted here.</p></section>
<div class="grid"><div class="card"><h3>Principal Identity</h3><p>Separate executive account and cookie namespace for the President, Vice President and Prime Minister.</p></div><div class="card"><h3>Encrypted Communications</h3><p>Protected executive messages encrypted before database storage.</p></div><div class="card"><h3>Cloud-First Archive</h3><p>Electronic capture of executive records, references and retention metadata.</p></div><div class="card"><h3>Private Workspace</h3><p>Dedicated digital study for principal-level work.</p></div><div class="card"><h3>Formal Boardroom</h3><p>Plan boardroom, private dining and secure conference sessions.</p></div><div class="card"><h3>Segregated Access</h3><p>Staff accounts cannot authenticate into this portal.</p></div></div>
<div class="two"><section class="panel" id="comms"><h3>Secure Communications</h3><form method="post" action="/executive/messages"><label>Recipient / channel</label><input name="recipient" required><label>Subject</label><input name="subject" required><label>Priority</label><select name="priority"><option>normal</option><option>high</option><option>urgent</option></select><label>Message</label><textarea name="message" required></textarea><button>Encrypt & Save</button></form><table><tr><th>ID</th><th>Recipient</th><th>Subject</th><th>Priority</th><th>Decrypted view</th></tr>{msg_rows}</table></section>
<section class="panel" id="archive"><h3>Executive Archive</h3><form method="post" action="/executive/archive"><label>Record title</label><input name="title" required><label>Reference</label><input name="record_reference"><label>Category</label><select name="category"><option>Executive Record</option><option>Briefing</option><option>Correspondence</option><option>Meeting Record</option><option>Digital Asset</option></select><label>Retention</label><select name="retention"><option>Permanent</option><option>Presidential Term</option><option>Operational</option></select><label>Protected notes</label><textarea name="notes"></textarea><button>Capture Record</button></form><table><tr><th>ID</th><th>Title</th><th>Category</th><th>Retention</th></tr>{arc_rows}</table></section></div>
<section class="panel" id="meetings" style="margin-top:18px"><h3>Boardroom / Private Suite Planner</h3><form method="post" action="/executive/meetings"><div class="two"><div><label>Title</label><input name="title" required><label>Type</label><select name="meeting_type"><option>Executive Boardroom</option><option>Private Dining</option><option>Presidential Study</option><option>Secure Video Conference</option></select><label>Scheduled for</label><input type="datetime-local" name="scheduled_for"></div><div><label>Guests</label><input name="guests"><label>Location / mode</label><select name="location_mode"><option>Private Boardroom</option><option>Private Dining Room</option><option>Executive Office</option><option>Secure Remote</option></select><label>Protected notes</label><textarea name="notes"></textarea></div></div><button>Schedule Executive Session</button></form><table><tr><th>ID</th><th>Title</th><th>Type</th><th>Scheduled</th><th>Location</th></tr>{mtg_rows}</table></section>"""
    return _shell(user, body)


async def create_message(request: Request):
    user=_principal(request)
    if not user: return RedirectResponse("/executive/login",303)
    form=await request.form(); recipient=str(form.get("recipient","")).strip(); subject=str(form.get("subject","")).strip(); message=str(form.get("message","")).strip(); priority=str(form.get("priority","normal")).strip()
    if not recipient or not subject or not message: raise HTTPException(400,"Required fields missing")
    token=_fernet().encrypt(message.encode()).decode()
    with core.db_cursor(commit=True) as cur:
        cur.execute("INSERT INTO executive_secure_messages(recipient,subject,ciphertext,priority,created_by,created_at) VALUES(?,?,?,?,?,?)",(recipient,subject,token,priority,user["account_id"],datetime.utcnow().isoformat()))
    return RedirectResponse("/executive#comms",303)


async def create_archive(request: Request):
    user=_principal(request)
    if not user: return RedirectResponse("/executive/login",303)
    form=await request.form(); title=str(form.get("title","")).strip(); ref=str(form.get("record_reference","")).strip(); category=str(form.get("category","Executive Record")); retention=str(form.get("retention","Permanent")); notes=str(form.get("notes","")).strip()
    if not title: raise HTTPException(400,"Title required")
    cipher=_fernet().encrypt(notes.encode()).decode() if notes else None
    with core.db_cursor(commit=True) as cur:
        cur.execute("INSERT INTO executive_archive(title,record_reference,category,retention,notes_ciphertext,created_by,created_at) VALUES(?,?,?,?,?,?,?)",(title,ref,category,retention,cipher,user["account_id"],datetime.utcnow().isoformat()))
    return RedirectResponse("/executive#archive",303)


async def create_meeting(request: Request):
    user=_principal(request)
    if not user: return RedirectResponse("/executive/login",303)
    form=await request.form(); title=str(form.get("title","")).strip(); mtype=str(form.get("meeting_type","Executive Boardroom")); scheduled=str(form.get("scheduled_for","")); guests=str(form.get("guests","")); location=str(form.get("location_mode","Private Boardroom")); notes=str(form.get("notes","")).strip()
    if not title: raise HTTPException(400,"Title required")
    cipher=_fernet().encrypt(notes.encode()).decode() if notes else None
    with core.db_cursor(commit=True) as cur:
        cur.execute("INSERT INTO executive_meetings(title,meeting_type,scheduled_for,guests,location_mode,notes_ciphertext,created_by,created_at) VALUES(?,?,?,?,?,?,?,?)",(title,mtype,scheduled,guests,location,cipher,user["account_id"],datetime.utcnow().isoformat()))
    return RedirectResponse("/executive#meetings",303)


def legacy_redirect():
    return RedirectResponse("/executive", status_code=303)


def apply_executive_suite(_core=None):
    init_schema()
    paths={"/executive","/executive/login","/executive/logout","/executive/setup","/executive/messages","/executive/archive","/executive/meetings","/admin/executive-suite"}
    core.app.router.routes[:] = [r for r in core.app.router.routes if getattr(r,"path",None) not in paths]
    core.app.add_api_route("/executive", dashboard, methods=["GET"], response_class=HTMLResponse)
    core.app.add_api_route("/executive/login", executive_login_form, methods=["GET"], response_class=HTMLResponse)
    core.app.add_api_route("/executive/login", executive_login, methods=["POST"])
    core.app.add_api_route("/executive/logout", executive_logout, methods=["GET"])
    core.app.add_api_route("/executive/setup", setup_form, methods=["GET"], response_class=HTMLResponse)
    core.app.add_api_route("/executive/setup", setup_submit, methods=["POST"])
    core.app.add_api_route("/executive/messages", create_message, methods=["POST"])
    core.app.add_api_route("/executive/archive", create_archive, methods=["POST"])
    core.app.add_api_route("/executive/meetings", create_meeting, methods=["POST"])
    core.app.add_api_route("/admin/executive-suite", legacy_redirect, methods=["GET"])
    return True
