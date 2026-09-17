"""Dedicated National Security Council workspace for UNG-PRESIDENT."""
from datetime import datetime, timezone
from html import escape
from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
_registered=False

def _now():return datetime.now(timezone.utc).isoformat()
def apply_nsc(appmod):
 global _registered
 app=appmod.app
 with appmod.db_cursor(commit=True) as cur:cur.execute("CREATE TABLE IF NOT EXISTS nsc_records(id INTEGER PRIMARY KEY AUTOINCREMENT,record_type TEXT NOT NULL,title TEXT NOT NULL,summary TEXT NOT NULL DEFAULT '',status TEXT NOT NULL DEFAULT 'open',classification TEXT NOT NULL DEFAULT 'restricted',owner TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL,updated_at TEXT NOT NULL)")
 if _registered:return app
 _registered=True
 modules=[('Presidential Briefings','briefing','Daily and rapid presidential national-security briefings'),('NSC Meetings & Agendas','meeting','Council agendas, schedules, papers, actions and decisions'),('Interagency Coordination','coordination','Foreign affairs, intelligence and defense coordination'),('Presidential Directives','directive','National-security decisions and implementation tracking'),('Situation Room','crisis','Crisis records and continuous executive updates'),('Analysis & Policy Options','analysis','Analytical reports, research and policy options'),('Leader & Summit Preparation','summit','Calls, summits and bilateral meeting preparation'),('Security Communications','communication','Authorized speeches and legislative/public briefings')]
 def auth(req):
  u=appmod.get_current_user(req);return u if u and str(u.get('role','')).lower() in {'admin','national_security','nsc'} else None
 def page(title,body):return f'<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{font-family:system-ui;background:#07111f;color:#edf4ff;margin:0}}header,main{{padding:24px}}header{{background:#0d1d31}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}}.card{{background:#10243a;border:1px solid #294968;border-radius:14px;padding:18px}}a{{color:#9fd0ff}}input,textarea,select{{width:100%;box-sizing:border-box;margin:6px 0 12px;padding:10px}}table{{width:100%}}td,th{{padding:9px;text-align:left}}</style></head><body><header><b>UNG-PRESIDENT · NATIONAL SECURITY COUNCIL</b> · <a href="/admin">Staff Admin</a> · <a href="/nsc">NSC Home</a></header><main><h1>{escape(title)}</h1>{body}</main></body></html>'
 @app.get('/nsc',response_class=HTMLResponse)
 async def home(request:Request):
  if not auth(request):return HTMLResponse('Forbidden',403)
  with appmod.db_cursor() as cur:cur.execute('SELECT record_type,COUNT(*) n FROM nsc_records GROUP BY record_type');counts={r['record_type']:r['n'] for r in cur.fetchall()}
  cards=''.join(f'<div class="card"><h3>{escape(l)}</h3><p>{escape(d)}</p><b>{counts.get(k,0)} records</b><p><a href="/nsc/{k}">Open workspace →</a></p></div>' for l,k,d in modules)
  return HTMLResponse(page('National Security Council','<p>Restricted presidential national-security coordination workspace.</p><div class="grid">'+cards+'</div>'))
 @app.get('/nsc/{kind}',response_class=HTMLResponse)
 async def list_records(request:Request,kind:str):
  if not auth(request):return HTMLResponse('Forbidden',403)
  valid={m[1]:m[0] for m in modules}
  if kind not in valid:return HTMLResponse('Not found',404)
  with appmod.db_cursor() as cur:cur.execute('SELECT * FROM nsc_records WHERE record_type=? ORDER BY id DESC',(kind,));rows=cur.fetchall()
  trs=''.join(f'<tr><td>{r["id"]}</td><td>{escape(r["title"])}</td><td>{escape(r["owner"])}</td><td>{escape(r["classification"])}</td><td>{escape(r["status"])}</td></tr>' for r in rows)
  body=f'<div class="card"><form method="post"><input name="title" placeholder="Title" required><textarea name="summary" placeholder="Summary / briefing" required></textarea><input name="owner" placeholder="Responsible office"><select name="classification"><option>restricted</option><option>confidential</option><option>secret</option><option>top-secret</option></select><button>Create record</button></form></div><h2>Records</h2><table><tr><th>ID</th><th>Title</th><th>Owner</th><th>Classification</th><th>Status</th></tr>{trs}</table>'
  return HTMLResponse(page(valid[kind],body))
 @app.post('/nsc/{kind}')
 async def create(request:Request,kind:str,title:str=Form(...),summary:str=Form(...),owner:str=Form(''),classification:str=Form('restricted')):
  if not auth(request):return HTMLResponse('Forbidden',403)
  if kind not in {m[1] for m in modules}:return HTMLResponse('Not found',404)
  if classification not in {'restricted','confidential','secret','top-secret'}:return HTMLResponse('Invalid classification',400)
  now=_now()
  with appmod.db_cursor(commit=True) as cur:cur.execute('INSERT INTO nsc_records(record_type,title,summary,status,classification,owner,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',(kind,title.strip(),summary.strip(),'open',classification,owner.strip(),now,now))
  return RedirectResponse(f'/nsc/{kind}',303)
 return app
