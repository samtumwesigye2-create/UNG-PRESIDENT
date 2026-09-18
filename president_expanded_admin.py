"""Operational expanded UNG-PRESIDENT admin modules layered on the production app."""
from datetime import datetime
from html import escape

from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

import ung_president as core
import president_expanded_data


MODULES = [
    ("Citizens Abroad", "/admin/citizens-abroad", "citizens_abroad"),
    ("Travel Advisories", "/admin/travel-advisories", "travel_advisories"),
    ("Emergency Alerts", "/admin/emergency-alerts", "emergency_alerts"),
    ("Missions", "/admin/missions", "diplomatic_missions"),
    ("Consular Queue", "/admin/consular", "consular_cases"),
    ("Media Accreditation", "/admin/media-accreditation", "media_accreditations"),
    ("Attestations", "/admin/attestations", "document_attestations"),
    ("Treaties / Archive", "/admin/treaties", "treaty_archive"),
    ("Approvals", "/admin/approvals", "approval_requests"),
    ("Biometrics", "/admin/biometrics", "biometric_enrollments"),
]

CONFIG = {
    "citizens_abroad": {
        "fields": [("full_name", "Full name", True), ("country", "Country", True), ("city", "City", False), ("passport_number", "Passport number", False), ("phone", "Phone", False), ("email", "Email", False), ("emergency_contact", "Emergency contact", False), ("status", "Status", False)],
        "search": ["full_name", "country", "city", "passport_number", "email"], "status": "status",
    },
    "travel_advisories": {
        "fields": [("country", "Country", True), ("level", "Level", True), ("title", "Title", True), ("summary", "Summary", True)],
        "search": ["country", "level", "title", "summary"], "status": "is_active", "auto": {"created_by": "user"},
    },
    "emergency_alerts": {
        "fields": [("title", "Title", True), ("message", "Message", True), ("severity", "Severity", True), ("audience", "Audience", False)],
        "search": ["title", "message", "severity", "audience"], "status": "is_active", "auto": {"created_by": "user"},
    },
    "diplomatic_missions": {
        "fields": [("mission_name", "Mission name", True), ("country", "Country", True), ("city", "City", False), ("mission_type", "Mission type", False), ("phone", "Phone", False), ("email", "Email", False), ("address", "Address", False), ("status", "Status", False)],
        "search": ["mission_name", "country", "city", "mission_type", "email"], "status": "status",
    },
    "consular_cases": {
        "fields": [("citizen_name", "Citizen name", True), ("country", "Country", True), ("case_type", "Case type", True), ("priority", "Priority", False), ("status", "Status", False), ("notes", "Notes", False)],
        "search": ["citizen_name", "country", "case_type", "priority", "status", "notes"], "status": "status",
    },
    "media_accreditations": {
        "fields": [("applicant_name", "Applicant name", True), ("organization", "Organization", True), ("email", "Email", False), ("phone", "Phone", False), ("event_name", "Event name", False), ("status", "Status", False)],
        "search": ["applicant_name", "organization", "email", "event_name", "status"], "status": "status",
    },
    "document_attestations": {
        "fields": [("applicant_name", "Applicant name", True), ("document_type", "Document type", True), ("reference_number", "Reference number", False), ("status", "Status", False), ("notes", "Notes", False)],
        "search": ["applicant_name", "document_type", "reference_number", "status", "notes"], "status": "status",
    },
    "treaty_archive": {
        "fields": [("title", "Title", True), ("partner", "Partner", False), ("signed_date", "Signed date", False), ("document_reference", "Document reference", False), ("status", "Status", False), ("notes", "Notes", False)],
        "search": ["title", "partner", "document_reference", "status", "notes"], "status": "status",
    },
    "approval_requests": {
        "fields": [("action_type", "Action type", True), ("subject_type", "Subject type", True), ("subject_id", "Subject ID", False), ("payload", "Payload / details", False)],
        "search": ["action_type", "subject_type", "payload", "status"], "auto": {"initiator_user_id": "user"},
    },
    "biometric_enrollments": {
        "fields": [("user_id", "User ID", True), ("modality", "Modality", True), ("device_id", "Device ID", False), ("external_reference", "External reference", False), ("template_hash", "Template hash", False), ("status", "Status", False)],
        "search": ["modality", "device_id", "external_reference", "status"], "status": "status", "auto": {"enrolled_by": "user"},
    },
}


def _user(request: Request):
    return core.admin_guard(request)


def _nav():
    return "".join(f'<a href="{path}">{escape(label)}</a>' for label, path, _ in MODULES)


def _shell(title: str, user, body: str):
    return HTMLResponse(f"""<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>{escape(title)} · UNG-PRESIDENT</title><style>
    body{{margin:0;background:#f6f3ec;color:#10203a;font-family:Arial,sans-serif}}aside{{position:fixed;inset:0 auto 0 0;width:250px;background:#07152a;padding:24px 18px;overflow:auto}}aside a{{display:block;color:#fff;text-decoration:none;padding:9px 0;font-size:14px}}main{{margin-left:286px;padding:30px;max-width:1180px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}}.card{{background:white;border:1px solid #ddd4c5;border-radius:10px;padding:18px}}h1{{border-bottom:2px solid #b5943d;padding-bottom:10px}}table{{width:100%;border-collapse:collapse;background:#fff;overflow:auto}}th,td{{padding:10px;border-bottom:1px solid #eee;text-align:left;font-size:13px;vertical-align:top}}input,textarea,select{{width:100%;box-sizing:border-box;padding:10px;border:1px solid #cfc7ba;border-radius:6px;font-size:15px}}textarea{{min-height:88px}}label{{font-size:13px;font-weight:700;display:block;margin-bottom:5px}}button{{padding:10px 14px;border:0;border-radius:6px;background:#10203a;color:white;font-weight:700}}.form-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}}.toolbar{{display:flex;gap:8px;align-items:end;flex-wrap:wrap;margin:12px 0}}.toolbar input{{min-width:230px}}.muted{{color:#667085}}.actions{{display:flex;gap:6px;flex-wrap:wrap}}.actions form{{display:inline}}.actions button{{padding:6px 9px;font-size:12px}}@media(max-width:760px){{aside{{position:relative;width:auto}}main{{margin-left:0;padding:18px}}table{{display:block;overflow-x:auto}}}}
    </style></head><body><aside><strong style='color:white'>UNG-PRESIDENT</strong><a href='/admin'>Dashboard</a>{_nav()}<a href='/admin/logout' style='color:#ff9a9a'>Logout</a></aside><main><h1>{escape(title)}</h1><p>Signed in as <strong>{escape(user['username'])}</strong> ({escape(user['role'])})</p>{body}</main></body></html>""")


def expanded_dashboard(request: Request):
    user = _user(request)
    cards = "".join(f'<a class="card" href="{path}"><strong>{escape(label)}</strong><p>Open module</p></a>' for label, path, _ in MODULES)
    old = [
        ("Digital Executive Suite","/admin/executive-suite"),
        ("Executive Orders","/admin/executive-orders"),("Appointments","/admin/appointments"),("National Honours","/admin/honours"),("Events & Protocol","/admin/events"),("Visit Requests","/admin/visit-requests"),("Citizen Petitions","/admin/petitions"),("State Visits","/admin/state-visits"),("Press Statements","/admin/press-statements"),("HR Verification Codes","/admin/hr-codes"),("Audit Log","/admin/audit-log")
    ]
    existing = "".join(f'<a class="card" href="{p}"><strong>{escape(l)}</strong></a>' for l,p in old)
    return _shell("Dashboard", user, f"<h2>Core Presidential Operations</h2><div class='grid'>{existing}</div><h2>Expanded Presidential Operations</h2><div class='grid'>{cards}</div>")


def _form(label, path, table):
    fields = CONFIG[table]["fields"]
    controls = []
    for name, field_label, required in fields:
        req = " required" if required else ""
        kind = "textarea" if name in {"summary", "message", "notes", "payload", "address", "emergency_contact"} else "input"
        if kind == "textarea":
            control = f'<textarea name="{escape(name)}"{req}></textarea>'
        else:
            input_type = "date" if name.endswith("_date") else "number" if name in {"subject_id", "user_id"} else "text"
            control = f'<input type="{input_type}" name="{escape(name)}"{req}>'
        controls.append(f'<div><label>{escape(field_label)}</label>{control}</div>')
    return f'<section class="card"><h2>Create new {escape(label)}</h2><form method="post" action="{path}"><div class="form-grid">{"".join(controls)}</div><p><button type="submit">Create record</button></p></form></section>'


def _search_clause(table: str, q: str):
    cols = CONFIG[table]["search"]
    if not q:
        return "", []
    clause = " OR ".join(f"CAST({c} AS TEXT) LIKE ?" for c in cols)
    return f" WHERE ({clause})", [f"%{q}%"] * len(cols)


def _record_actions(path: str, table: str, row):
    if table == "approval_requests":
        if row["status"] != "pending":
            return escape(str(row["status"]))
        return f'''<div class="actions"><form method="post" action="{path}/{row['id']}/decision"><input type="hidden" name="decision" value="approved"><input type="hidden" name="decision_note" value="Approved in PRESIDENT"><button>Approve</button></form><form method="post" action="{path}/{row['id']}/decision"><input type="hidden" name="decision" value="rejected"><input type="hidden" name="decision_note" value="Rejected in PRESIDENT"><button>Reject</button></form></div>'''
    status_col = CONFIG[table].get("status")
    if not status_col:
        return ""
    if status_col == "is_active":
        options = [("1", "Activate"), ("0", "Deactivate")]
    else:
        options = [("active", "Active"), ("pending", "Pending"), ("open", "Open"), ("approved", "Approve"), ("rejected", "Reject"), ("closed", "Close"), ("revoked", "Revoke")]
    buttons = "".join(f'<form method="post" action="{path}/{row["id"]}/status"><input type="hidden" name="status" value="{v}"><button>{escape(label)}</button></form>' for v, label in options)
    return f'<div class="actions">{buttons}</div>'


def _list_page(label, path, table, request):
    user = _user(request)
    q = (request.query_params.get("q") or "").strip()
    where, params = _search_clause(table, q)
    with core.db_cursor() as cur:
        cur.execute(f"SELECT * FROM {table}{where} ORDER BY id DESC LIMIT 100", params)
        rows = cur.fetchall()
    search = f'''<form class="toolbar" method="get" action="{path}"><div><label>Search</label><input name="q" value="{escape(q)}" placeholder="Search records"></div><button type="submit">Search</button><a href="{path}">Clear</a></form>'''
    create = _form(label, path, table)
    if rows:
        cols = rows[0].keys()
        head = ''.join(f'<th>{escape(c)}</th>' for c in cols) + '<th>Actions</th>'
        body = ''.join('<tr>'+''.join(f'<td>{escape(str(r[c] if r[c] is not None else ""))}</td>' for c in cols)+f'<td>{_record_actions(path, table, r)}</td></tr>' for r in rows)
        content = f'<p>{len(rows)} record(s)</p><div style="overflow:auto"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
    else:
        content = '<div class="card"><strong>No matching records.</strong><p class="muted">Use the form above to create the first operational record.</p></div>'
    return _shell(label, user, create + search + content)


async def _create_record(table: str, path: str, request: Request):
    user = _user(request)
    form = await request.form()
    config = CONFIG[table]
    values = {}
    for name, _, required in config["fields"]:
        raw = str(form.get(name, "")).strip()
        if required and not raw:
            raise HTTPException(status_code=400, detail=f"{name} is required")
        if raw:
            values[name] = raw
    for name, source in config.get("auto", {}).items():
        values[name] = user["user_id"] if source == "user" else source
    if table == "approval_requests":
        values["status"] = "pending"
    if table in {"travel_advisories", "emergency_alerts"}:
        values.setdefault("is_active", 1)
    columns = list(values)
    placeholders = ",".join("?" for _ in columns)
    with core.db_cursor(commit=True) as cur:
        cur.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})", [values[c] for c in columns])
        record_id = cur.lastrowid
    core.log_action(user["user_id"], user["username"], f"create_{table}", table, record_id)
    return RedirectResponse(path, status_code=303)


async def _update_status(table: str, path: str, record_id: int, request: Request):
    user = _user(request)
    status_col = CONFIG[table].get("status")
    if not status_col:
        raise HTTPException(status_code=400, detail="This module has no direct status update")
    form = await request.form()
    status = str(form.get("status", "")).strip()
    if not status:
        raise HTTPException(status_code=400, detail="status is required")
    extras = []
    params = [status]
    if table == "consular_cases":
        extras.append("updated_at=?")
        params.append(datetime.utcnow().isoformat())
    if table in {"media_accreditations", "document_attestations"}:
        reviewer_col = "reviewed_by"
        extras.append(f"{reviewer_col}=?")
        params.append(user["user_id"])
    set_clause = f"{status_col}=?" + ("," + ",".join(extras) if extras else "")
    params.append(record_id)
    with core.db_cursor(commit=True) as cur:
        cur.execute(f"UPDATE {table} SET {set_clause} WHERE id=?", params)
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Record not found")
    core.log_action(user["user_id"], user["username"], f"update_{table}_status", table, record_id, detail=status)
    return RedirectResponse(path, status_code=303)


async def _approval_decision(path: str, request_id: int, request: Request):
    user = _user(request)
    form = await request.form()
    decision = str(form.get("decision", "")).strip().lower()
    note = str(form.get("decision_note", "")).strip()
    if decision not in {"approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Decision must be approved or rejected")
    with core.db_cursor() as cur:
        cur.execute("SELECT * FROM approval_requests WHERE id=?", (request_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Approval request not found")
    if row["status"] != "pending":
        raise HTTPException(status_code=409, detail="Approval request already decided")
    if row["initiator_user_id"] == user["user_id"]:
        raise HTTPException(status_code=400, detail="Initiator cannot approve or reject their own request")
    with core.db_cursor(commit=True) as cur:
        cur.execute("UPDATE approval_requests SET status=?, approver_user_id=?, decision_note=?, decided_at=? WHERE id=? AND status='pending'", (decision, user["user_id"], note, datetime.utcnow().isoformat(), request_id))
    core.log_action(user["user_id"], user["username"], f"approval_{decision}", "approval_requests", request_id, detail=note)
    return RedirectResponse(path, status_code=303)


def _remove_get_admin():
    core.app.router.routes[:] = [r for r in core.app.router.routes if not (getattr(r, 'path', None) == '/admin' and 'GET' in getattr(r, 'methods', set()))]


def _remove_expanded_routes():
    expanded_paths = {"/admin"}
    for _, path, _ in MODULES:
        expanded_paths.update({path, path + "/{record_id}/status", path + "/{request_id}/decision"})
    core.app.router.routes[:] = [r for r in core.app.router.routes if not (getattr(r, 'path', None) in expanded_paths and any(m in getattr(r, 'methods', set()) for m in {"GET", "POST"}))]


def apply_expanded_admin():
    president_expanded_data.init_expanded_schema()
    _remove_expanded_routes()
    _remove_get_admin()
    core.app.add_api_route('/admin', expanded_dashboard, methods=['GET'], response_class=HTMLResponse)
    for label, path, table in MODULES:
        def get_handler(request: Request, _label=label, _path=path, _table=table):
            return _list_page(_label, _path, _table, request)
        async def post_handler(request: Request, _table=table, _path=path):
            return await _create_record(_table, _path, request)
        async def status_handler(record_id: int, request: Request, _table=table, _path=path):
            return await _update_status(_table, _path, record_id, request)
        core.app.add_api_route(path, get_handler, methods=['GET'], response_class=HTMLResponse)
        core.app.add_api_route(path, post_handler, methods=['POST'])
        if CONFIG[table].get("status"):
            core.app.add_api_route(path + '/{record_id}/status', status_handler, methods=['POST'])
        if table == "approval_requests":
            async def decision_handler(request_id: int, request: Request, _path=path):
                return await _approval_decision(_path, request_id, request)
            core.app.add_api_route(path + '/{request_id}/decision', decision_handler, methods=['POST'])
    return True
