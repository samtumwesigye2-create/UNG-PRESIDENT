"""Uganda-focused United Nations affairs workspace for UNG-PRESIDENT."""
from html import escape
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
import ung_president as core

DUTIES = [
    ("Uganda Representation & Negotiations", "Represent Uganda in United Nations bodies and manage negotiating positions."),
    ("Leadership & NSC Briefings", "Prepare UN and geopolitical updates for the President, responsible foreign-affairs leadership and, where national security is involved, the National Security Council."),
    ("Diplomatic Engagement", "Record engagement with foreign missions and United Nations officials and coordinate lawful coalition-building around Uganda's stated positions."),
    ("Uganda Mission Management", "Coordinate mission personnel and legal, security, economic and public-diplomacy work."),
    ("Resolutions & Voting", "Track draft resolutions, amendments, Uganda's voting position and negotiation history without implying a permanent Security Council veto."),
    ("Multilateral Policy", "Track Uganda's participation in General Assembly and other multilateral declarations, frameworks and norm-setting processes."),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS un_affairs_records (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 workstream TEXT NOT NULL,
 title TEXT NOT NULL,
 un_body TEXT,
 country_or_organization TEXT,
 document_reference TEXT,
 uganda_position TEXT,
 voting_position TEXT,
 nsc_relevance INTEGER NOT NULL DEFAULT 0,
 owner TEXT,
 status TEXT NOT NULL DEFAULT 'open',
 notes TEXT,
 created_by INTEGER,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

def apply_un_affairs(appmod=core):
    with appmod.db_cursor(commit=True) as cur:
        cur.execute(SCHEMA)
    app = appmod.app

    @app.get('/admin/un-affairs', response_class=HTMLResponse)
    async def un_affairs(request: Request):
        user = appmod.admin_guard(request)
        with appmod.db_cursor() as cur:
            cur.execute('SELECT * FROM un_affairs_records ORDER BY id DESC LIMIT 100')
            rows = cur.fetchall()
        cards = ''.join(f'<div class="card"><strong>{escape(a)}</strong><p>{escape(b)}</p></div>' for a,b in DUTIES)
        records = ''.join(f'<tr><td>{r["id"]}</td><td>{escape(r["workstream"])}</td><td>{escape(r["title"])}</td><td>{escape(r["un_body"] or "")}</td><td>{escape(r["uganda_position"] or "")}</td><td>{escape(r["voting_position"] or "")}</td><td>{"Yes" if r["nsc_relevance"] else "No"}</td><td>{escape(r["status"])}</td></tr>' for r in rows)
        body=f'''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>UN Affairs · UNG-PRESIDENT</title><style>body{{font-family:Arial;background:#f6f3ec;color:#10203a;margin:0}}header{{background:#07152a;color:white;padding:22px}}main{{max-width:1200px;margin:auto;padding:24px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}}.card{{background:white;border:1px solid #ddd4c5;border-radius:10px;padding:16px}}input,textarea,select{{width:100%;box-sizing:border-box;padding:9px;margin:4px 0 10px}}table{{width:100%;border-collapse:collapse;background:white}}td,th{{padding:8px;border-bottom:1px solid #ddd;text-align:left}}a{{color:#9fd0ff}}</style></head><body><header><b>UNG-PRESIDENT · FOREIGN AFFAIRS & DIPLOMACY · UN AFFAIRS</b> &nbsp; <a href="/admin">Admin</a> &nbsp; <a href="/nsc">NSC</a></header><main><h1>Uganda Mission to the United Nations / UN Affairs</h1><div class="grid">{cards}</div><div class="card"><h2>Create UN Affairs Record</h2><form method="post"><label>Workstream</label><select name="workstream">{''.join(f'<option>{escape(x[0])}</option>' for x in DUTIES)}</select><label>Title</label><input name="title" required><label>UN body</label><input name="un_body" placeholder="e.g. General Assembly"><label>Country / organization</label><input name="country_or_organization"><label>Document / resolution reference</label><input name="document_reference"><label>Uganda position</label><textarea name="uganda_position"></textarea><label>Voting position</label><select name="voting_position"><option value="">Not applicable / undecided</option><option>For</option><option>Against</option><option>Abstain</option><option>Not voting</option></select><label><input style="width:auto" type="checkbox" name="nsc_relevance" value="1"> National-security relevance / route to NSC</label><label>Owner</label><input name="owner"><label>Notes</label><textarea name="notes"></textarea><button>Create record</button></form></div><h2>Operational Records</h2><table><tr><th>ID</th><th>Workstream</th><th>Title</th><th>UN body</th><th>Uganda position</th><th>Vote</th><th>NSC</th><th>Status</th></tr>{records}</table></main></body></html>'''
        return HTMLResponse(body)

    @app.post('/admin/un-affairs')
    async def create_un_affairs(request: Request):
        user = appmod.admin_guard(request)
        form = await request.form()
        title = str(form.get('title','')).strip()
        workstream = str(form.get('workstream','')).strip()
        if not title or workstream not in {x[0] for x in DUTIES}:
            raise HTTPException(status_code=400, detail='Valid workstream and title are required')
        voting = str(form.get('voting_position','')).strip()
        if voting not in {'','For','Against','Abstain','Not voting'}:
            raise HTTPException(status_code=400, detail='Invalid voting position')
        vals=(workstream,title,str(form.get('un_body','')).strip(),str(form.get('country_or_organization','')).strip(),str(form.get('document_reference','')).strip(),str(form.get('uganda_position','')).strip(),voting,1 if form.get('nsc_relevance') else 0,str(form.get('owner','')).strip(),str(form.get('notes','')).strip(),user['user_id'])
        with appmod.db_cursor(commit=True) as cur:
            cur.execute('INSERT INTO un_affairs_records(workstream,title,un_body,country_or_organization,document_reference,uganda_position,voting_position,nsc_relevance,owner,notes,created_by) VALUES(?,?,?,?,?,?,?,?,?,?,?)', vals)
            rid=cur.lastrowid
        appmod.log_action(user['user_id'],user['username'],'create_un_affairs','un_affairs_records',rid)
        return RedirectResponse('/admin/un-affairs',status_code=303)
    return app
