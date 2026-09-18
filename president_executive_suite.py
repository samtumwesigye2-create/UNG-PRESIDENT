"""UNG-PRESIDENT Digital Executive Suite."""
import base64
import hashlib
from datetime import datetime
from html import escape

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

import ung_president as core


def _fernet(core):
    secret = (core.SECRET_KEY or "development-only").encode()
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(key)


def _user(core, request: Request):
    user = core.admin_guard(request)
    if user["role"] not in {"admin", "president"}:
        raise HTTPException(status_code=403, detail="Digital Executive Suite access is restricted")
    return user


def init_schema(core):
    with core.db_cursor(commit=True) as cur:
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


def _decrypt(fernet, value):
    if not value:
        return ""
    try:
        return fernet.decrypt(value.encode()).decode()
    except (InvalidToken, ValueError):
        return "[unavailable]"


def _shell(user, body):
    return HTMLResponse(f"""<!doctype html><html><head>
<meta name="viewport" content="width=1180,initial-scale=1">
<title>Digital Executive Suite · UNG-PRESIDENT</title>
<style>
*{{box-sizing:border-box}}html,body{{margin:0;min-width:1180px;background:#07111f;color:#eaf0f6;font-family:Arial,sans-serif}}
body{{overflow-x:auto}}.top{{height:100px;background:linear-gradient(90deg,#061529,#0b2948);border-bottom:2px solid #caa447;display:flex;align-items:center;justify-content:space-between;padding:0 34px}}
.brand{{display:flex;gap:16px;align-items:center}}.seal{{width:64px;height:64px;border:2px solid #caa447;border-radius:50%;display:grid;place-items:center;font-family:Georgia,serif;color:#e7c76b;font-size:26px}}
.brand h1{{font-family:Georgia,serif;margin:0;font-size:27px;letter-spacing:1px}}.brand small{{color:#d5b761;letter-spacing:2px}}
.user{{text-align:right;font-size:13px;color:#b8c5d3}}.layout{{display:grid;grid-template-columns:250px 1fr;min-height:calc(100vh - 100px)}}
aside{{background:#081827;border-right:1px solid #20364d;padding:28px 20px}}aside a{{display:block;color:#dfe8f1;text-decoration:none;padding:11px 12px;border-radius:7px;margin-bottom:5px}}aside a:hover{{background:#102b47;color:#f2cf69}}
main{{padding:32px 34px;max-width:1450px}}.hero{{background:linear-gradient(120deg,#0e2d4c,#102039);border:1px solid #2a435d;border-radius:16px;padding:30px;box-shadow:0 12px 30px #02070d88}}
.hero h2{{font-family:Georgia,serif;font-size:31px;margin:0 0 8px;color:#fff}}.hero p{{margin:0;color:#b8c7d6;max-width:800px}}.gold{{color:#d6b354}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:18px}}.card{{background:#0c1d2e;border:1px solid #233b53;border-radius:13px;padding:19px;box-shadow:0 6px 16px #0005}}.card h3{{margin:0 0 8px;color:#f0cc67;font-size:15px}}.card p{{margin:0;color:#aebdcb;font-size:13px;line-height:1.45}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:18px}}.panel{{background:#0b1a2a;border:1px solid #22384e;border-radius:13px;padding:20px}}h3{{margin-top:0}}
label{{display:block;font-size:12px;color:#c9d3dd;margin:10px 0 5px;font-weight:700}}input,textarea,select{{width:100%;background:#07131f;color:#eef3f8;border:1px solid #334a61;border-radius:7px;padding:10px}}textarea{{min-height:88px}}button{{margin-top:12px;background:#c7a247;color:#07111f;border:0;border-radius:7px;padding:10px 14px;font-weight:800;cursor:pointer}}
table{{width:100%;border-collapse:collapse;margin-top:12px;font-size:12px}}th,td{{padding:9px;border-bottom:1px solid #24384b;text-align:left;vertical-align:top}}th{{color:#d9ba61}}.tag{{display:inline-block;padding:3px 7px;border:1px solid #3a536d;border-radius:10px;color:#a8bbce;font-size:10px}}
.status{{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}}.pill{{background:#0b2237;border:1px solid #2f4a65;border-radius:99px;padding:8px 11px;font-size:11px;color:#c9d5e1}}
</style></head><body>
<div class="top"><div class="brand"><div class="seal">P</div><div><h1>DIGITAL EXECUTIVE SUITE</h1><small>UNG-PRESIDENT · REPUBLIC OF UGANDA</small></div></div><div class="user">SIGNED IN<br><strong>{escape(user["username"])}</strong> · {escape(user["role"])}</div></div>
<div class="layout"><aside><a href="/admin">← Presidential Dashboard</a><a href="/admin/executive-suite">Executive Suite Home</a><a href="#comms">Secure Communications</a><a href="#archive">Executive Archive</a><a href="#meetings">Boardroom & Meetings</a><a href="/admin/audit-log">Audit Log</a><a href="/admin/logout" style="color:#ff9b9b">Logout</a></aside><main>{body}</main></div>
</body></html>""")


def dashboard(core, request: Request):
    user = _user(core, request)
    f = _fernet(core)
    with core.db_cursor() as cur:
        cur.execute("SELECT * FROM executive_secure_messages ORDER BY id DESC LIMIT 8")
        messages = cur.fetchall()
        cur.execute("SELECT * FROM executive_archive ORDER BY id DESC LIMIT 8")
        archive = cur.fetchall()
        cur.execute("SELECT * FROM executive_meetings ORDER BY id DESC LIMIT 8")
        meetings = cur.fetchall()

    msg_rows = "".join(
        f"<tr><td>{r['id']}</td><td>{escape(r['recipient'])}</td><td>{escape(r['subject'])}</td><td>{escape(r['priority'])}</td><td>{escape(r['created_at'])}</td><td>{escape(_decrypt(f,r['ciphertext'])[:120])}</td></tr>"
        for r in messages
    ) or "<tr><td colspan='6'>No secure messages yet.</td></tr>"
    arc_rows = "".join(
        f"<tr><td>{r['id']}</td><td>{escape(r['title'])}</td><td>{escape(r['category'])}</td><td>{escape(r['retention'])}</td><td>{escape(r['record_reference'] or '')}</td></tr>"
        for r in archive
    ) or "<tr><td colspan='5'>No archived records yet.</td></tr>"
    meeting_rows = "".join(
        f"<tr><td>{r['id']}</td><td>{escape(r['title'])}</td><td>{escape(r['meeting_type'])}</td><td>{escape(r['scheduled_for'] or '')}</td><td>{escape(r['location_mode'])}</td><td>{escape(r['guests'] or '')}</td></tr>"
        for r in meetings
    ) or "<tr><td colspan='6'>No executive meetings scheduled.</td></tr>"

    body=f"""
<section class="hero"><h2>Presidential <span class="gold">Digital Executive Suite</span></h2><p>A private command workspace combining identity-controlled access, encrypted executive communications, electronic records capture, boardroom planning, and high-aesthetic presidential operations.</p>
<div class="status"><span class="pill">Identity: authenticated session</span><span class="pill">Communications: encrypted at rest</span><span class="pill">Archive: real-time database capture</span><span class="pill">Access: President / Administrator only</span><span class="pill">Audit logging enabled</span></div></section>
<div class="grid">
 <div class="card"><h3>Universal Sign-On</h3><p>One authenticated presidential session across suite functions. External identity-provider federation can be connected through JANUS without changing the suite workflow.</p></div>
 <div class="card"><h3>Encrypted Communications</h3><p>Executive message bodies are encrypted before database storage using a key derived from the persistent presidential application secret.</p></div>
 <div class="card"><h3>Cloud-First Records</h3><p>Records and executive archive entries are captured electronically with timestamps, references, retention labels and audit history.</p></div>
 <div class="card"><h3>Private Workspace</h3><p>Restricted digital study for presidential work, executive notes and confidential workflow management.</p></div>
 <div class="card"><h3>Formal Boardroom</h3><p>Schedule executive meetings, private dining/boardroom sessions and remote conferences for up to 10 principal guests.</p></div>
 <div class="card"><h3>Privacy & Support Zones</h3><p>Role-gated access model designed to separate principal, senior staff and support functions instead of exposing the entire suite to every staff account.</p></div>
</div>
<div class="two">
<section class="panel" id="comms"><h3>Secure Communications</h3><form method="post" action="/admin/executive-suite/messages">
<label>Recipient / channel</label><input name="recipient" required maxlength="120">
<label>Subject</label><input name="subject" required maxlength="160">
<label>Priority</label><select name="priority"><option>normal</option><option>high</option><option>urgent</option></select>
<label>Encrypted message</label><textarea name="message" required maxlength="5000"></textarea><button>Encrypt & Save</button></form>
<table><tr><th>ID</th><th>Recipient</th><th>Subject</th><th>Priority</th><th>Created</th><th>Decrypted view</th></tr>{msg_rows}</table></section>
<section class="panel" id="archive"><h3>Executive Archive</h3><form method="post" action="/admin/executive-suite/archive">
<label>Record title</label><input name="title" required maxlength="180"><label>Reference</label><input name="record_reference" maxlength="100">
<label>Category</label><select name="category"><option>Executive Record</option><option>Briefing</option><option>Correspondence</option><option>Meeting Record</option><option>Digital Asset</option></select>
<label>Retention</label><select name="retention"><option>Permanent</option><option>Presidential Term</option><option>Operational</option></select>
<label>Protected notes</label><textarea name="notes" maxlength="3000"></textarea><button>Capture Record</button></form>
<table><tr><th>ID</th><th>Title</th><th>Category</th><th>Retention</th><th>Reference</th></tr>{arc_rows}</table></section>
</div>
<section class="panel" id="meetings" style="margin-top:18px"><h3>Formal Entertaining / Boardroom Planner</h3><form method="post" action="/admin/executive-suite/meetings">
<div class="two"><div><label>Meeting / dinner title</label><input name="title" required maxlength="180"><label>Type</label><select name="meeting_type"><option>Executive Boardroom</option><option>Private Dining</option><option>Presidential Study</option><option>Secure Video Conference</option></select><label>Scheduled for</label><input type="datetime-local" name="scheduled_for"></div>
<div><label>Principal guests (8–10 recommended)</label><input name="guests" maxlength="500"><label>Location / mode</label><select name="location_mode"><option>Private Boardroom</option><option>Private Dining Room</option><option>Executive Office</option><option>Secure Remote</option></select><label>Protected notes</label><textarea name="notes" maxlength="3000"></textarea></div></div><button>Schedule Executive Session</button></form>
<table><tr><th>ID</th><th>Title</th><th>Type</th><th>Scheduled</th><th>Location</th><th>Guests</th></tr>{meeting_rows}</table></section>
"""
    return _shell(user, body)


async def create_message(core, request: Request):
    user=_user(core, request); form=await request.form()
    recipient=str(form.get("recipient","")).strip(); subject=str(form.get("subject","")).strip(); message=str(form.get("message","")).strip(); priority=str(form.get("priority","normal")).strip()
    if not recipient or not subject or not message: raise HTTPException(status_code=400, detail="Recipient, subject and message are required")
    token=_fernet(core).encrypt(message.encode()).decode()
    with core.db_cursor(commit=True) as cur:
        cur.execute("INSERT INTO executive_secure_messages(recipient,subject,ciphertext,priority,created_by,created_at) VALUES(?,?,?,?,?,?)",(recipient,subject,token,priority,user["user_id"],datetime.utcnow().isoformat()))
        rid=cur.lastrowid
    core.log_action(user["user_id"],user["username"],"executive_secure_message_create","executive_secure_messages",rid,detail=subject)
    return RedirectResponse("/admin/executive-suite#comms",status_code=303)


async def create_archive(core, request: Request):
    user=_user(core, request); form=await request.form()
    title=str(form.get("title","")).strip(); ref=str(form.get("record_reference","")).strip(); category=str(form.get("category","Executive Record")).strip(); retention=str(form.get("retention","Permanent")).strip(); notes=str(form.get("notes","")).strip()
    if not title: raise HTTPException(status_code=400, detail="Title is required")
    cipher=_fernet(core).encrypt(notes.encode()).decode() if notes else None
    with core.db_cursor(commit=True) as cur:
        cur.execute("INSERT INTO executive_archive(title,record_reference,category,retention,notes_ciphertext,created_by,created_at) VALUES(?,?,?,?,?,?,?)",(title,ref,category,retention,cipher,user["user_id"],datetime.utcnow().isoformat()))
        rid=cur.lastrowid
    core.log_action(user["user_id"],user["username"],"executive_archive_capture","executive_archive",rid,detail=title)
    return RedirectResponse("/admin/executive-suite#archive",status_code=303)


async def create_meeting(core, request: Request):
    user=_user(core, request); form=await request.form()
    title=str(form.get("title","")).strip(); mtype=str(form.get("meeting_type","Executive Boardroom")).strip(); scheduled=str(form.get("scheduled_for","")).strip(); guests=str(form.get("guests","")).strip(); location=str(form.get("location_mode","Private Boardroom")).strip(); notes=str(form.get("notes","")).strip()
    if not title: raise HTTPException(status_code=400, detail="Title is required")
    cipher=_fernet(core).encrypt(notes.encode()).decode() if notes else None
    with core.db_cursor(commit=True) as cur:
        cur.execute("INSERT INTO executive_meetings(title,meeting_type,scheduled_for,guests,location_mode,notes_ciphertext,created_by,created_at) VALUES(?,?,?,?,?,?,?,?)",(title,mtype,scheduled,guests,location,cipher,user["user_id"],datetime.utcnow().isoformat()))
        rid=cur.lastrowid
    core.log_action(user["user_id"],user["username"],"executive_meeting_schedule","executive_meetings",rid,detail=title)
    return RedirectResponse("/admin/executive-suite#meetings",status_code=303)


def suite_home(request: Request):
    try:
        return dashboard(core, request)
    except HTTPException as exc:
        if exc.status_code in {401, 403}:
            return RedirectResponse("/admin/login", status_code=303)
        raise


async def suite_message(request: Request):
    return await create_message(core, request)


async def suite_archive(request: Request):
    return await create_archive(core, request)


async def suite_meeting(request: Request):
    return await create_meeting(core, request)


def apply_executive_suite(_core=None):
    init_schema(core)
    owned = {
        "/admin/executive-suite",
        "/admin/executive-suite/messages",
        "/admin/executive-suite/archive",
        "/admin/executive-suite/meetings",
    }
    core.app.router.routes[:] = [
        r for r in core.app.router.routes
        if getattr(r, "path", None) not in owned
    ]
    core.app.add_api_route("/admin/executive-suite", suite_home, methods=["GET"], response_class=HTMLResponse)
    core.app.add_api_route("/admin/executive-suite/messages", suite_message, methods=["POST"])
    core.app.add_api_route("/admin/executive-suite/archive", suite_archive, methods=["POST"])
    core.app.add_api_route("/admin/executive-suite/meetings", suite_meeting, methods=["POST"])
    return True
