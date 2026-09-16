"""Expanded UNG-PRESIDENT admin modules layered on the current production app."""
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


def _user(request: Request):
    return core.admin_guard(request)


def _nav():
    return "".join(f'<a href="{path}">{escape(label)}</a>' for label, path, _ in MODULES)


def _shell(title: str, user, body: str):
    return HTMLResponse(f"""<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>{escape(title)} · UNG-PRESIDENT</title><style>
    body{{margin:0;background:#f6f3ec;color:#10203a;font-family:Arial,sans-serif}}aside{{position:fixed;inset:0 auto 0 0;width:250px;background:#07152a;padding:24px 18px;overflow:auto}}aside a{{display:block;color:#fff;text-decoration:none;padding:9px 0;font-size:14px}}main{{margin-left:286px;padding:30px;max-width:1100px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}}.card{{background:white;border:1px solid #ddd4c5;border-radius:8px;padding:18px}}h1{{border-bottom:2px solid #b5943d;padding-bottom:10px}}table{{width:100%;border-collapse:collapse;background:#fff}}th,td{{padding:10px;border-bottom:1px solid #eee;text-align:left;font-size:13px}}@media(max-width:760px){{aside{{position:relative;width:auto}}main{{margin-left:0;padding:18px}}}}
    </style></head><body><aside><strong style='color:white'>UNG-PRESIDENT</strong><a href='/admin'>Dashboard</a>{_nav()}<a href='/admin/logout' style='color:#ff9a9a'>Logout</a></aside><main><h1>{escape(title)}</h1><p>Signed in as <strong>{escape(user['username'])}</strong> ({escape(user['role'])})</p>{body}</main></body></html>""")


def expanded_dashboard(request: Request):
    user = _user(request)
    cards = "".join(f'<a class="card" href="{path}"><strong>{escape(label)}</strong><p>Open module</p></a>' for label, path, _ in MODULES)
    old = [
        ("Executive Orders","/admin/executive-orders"),("Appointments","/admin/appointments"),("National Honours","/admin/honours"),("Events & Protocol","/admin/events"),("Visit Requests","/admin/visit-requests"),("Citizen Petitions","/admin/petitions"),("State Visits","/admin/state-visits"),("Press Statements","/admin/press-statements"),("HR Verification Codes","/admin/hr-codes"),("Audit Log","/admin/audit-log")
    ]
    existing = "".join(f'<a class="card" href="{p}"><strong>{escape(l)}</strong></a>' for l,p in old)
    return _shell("Dashboard", user, f"<h2>Core Presidential Operations</h2><div class='grid'>{existing}</div><h2>Expanded Presidential Operations</h2><div class='grid'>{cards}</div>")


def _list_page(label, table, request):
    user = _user(request)
    with core.db_cursor() as cur:
        cur.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 100")
        rows = cur.fetchall()
    if rows:
        cols = rows[0].keys()
        head = ''.join(f'<th>{escape(c)}</th>' for c in cols)
        body = ''.join('<tr>'+''.join(f'<td>{escape(str(r[c] if r[c] is not None else ""))}</td>' for c in cols)+'</tr>' for r in rows)
        content = f'<p>{len(rows)} record(s)</p><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'
    else:
        content = '<div class="card"><strong>No records yet.</strong><p>This module is connected to persistent storage and ready for operational records.</p></div>'
    return _shell(label, user, content)


def _remove_get_admin():
    core.app.router.routes[:] = [r for r in core.app.router.routes if not (getattr(r, 'path', None) == '/admin' and 'GET' in getattr(r, 'methods', set()))]


def apply_expanded_admin():
    president_expanded_data.init_expanded_schema()
    _remove_get_admin()
    core.app.add_api_route('/admin', expanded_dashboard, methods=['GET'], response_class=HTMLResponse)
    for label, path, table in MODULES:
        def handler(request: Request, _label=label, _table=table):
            return _list_page(_label, _table, request)
        core.app.add_api_route(path, handler, methods=['GET'], response_class=HTMLResponse)
    return True
