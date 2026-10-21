"""Dedicated National Security Council workspace for UNG-PRESIDENT."""
from datetime import datetime, timezone
from html import escape
from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
_registered=False

def _now(): return datetime.now(timezone.utc).isoformat()
def apply_nsc(appmod):
 global _registered
 app=appmod.app
 with appmod.db_cursor(commit=True) as cur:
  cur.execute("CREATE TABLE IF NOT EXISTS nsc_records(id INTEGER PRIMARY KEY AUTOINCREMENT,record_type TEXT NOT NULL,title TEXT NOT NULL,summary TEXT NOT NULL DEFAULT '',status TEXT NOT NULL DEFAULT 'open',classification TEXT NOT NULL DEFAULT 'restricted',owner TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL,updated_at TEXT NOT NULL)")
  cols={r['name'] for r in cur.execute('PRAGMA table_info(nsc_records)').fetchall()}
  if 'priority' not in cols: cur.execute("ALTER TABLE nsc_records ADD COLUMN priority TEXT NOT NULL DEFAULT 'normal'")
  if 'due_date' not in cols: cur.execute("ALTER TABLE nsc_records ADD COLUMN due_date TEXT NOT NULL DEFAULT ''")
 if _registered:return app
 _registered=True
 modules=[('Presidential Briefings','briefing','Daily and rapid presidential national-security briefings'),('NSC Meetings & Agendas','meeting','Council agendas, schedules, papers, actions and decisions'),('Interagency Coordination','coordination','Foreign affairs, intelligence and defense coordination'),('Presidential Directives','directive','National-security decisions and implementation tracking'),('Situation Room','crisis','Crisis records and continuous executive updates'),('Analysis & Policy Options','analysis','Analytical reports, research and policy options'),('Leader & Summit Preparation','summit','Calls, summits and bilateral meeting preparation'),('Security Communications','communication','Authorized speeches and legislative/public briefings')]
 def auth(req):
  u=appmod.get_current_user(req);return u if u and str(u.get('role','')).lower() in {'admin','president','national_security','nsc'} else None
 def page(title,body):
  seal=getattr(appmod,'PRES_SEAL_B64','')
  return f'''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} · UNG-PRESIDENT</title><style>body{{font-family:Arial,sans-serif;background:#07111f;color:#edf4ff;margin:0}}header{{background:#0d1d31;padding:18px 24px;display:flex;align-items:center;gap:14px;flex-wrap:wrap}}header img{{width:58px;height:58px;border-radius:50%;object-fit:cover;border:2px solid #c9a94b}}header .brand{{font-weight:800;font-size:18px;letter-spacing:.4px}}nav a{{color:#a9d4ff;margin-right:12px}}main{{padding:28px;max-width:1200px;margin:auto}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}}.card{{background:#10243a;border:1px solid #365879;border-radius:14px;padding:18px;margin-bottom:18px}}a{{color:#a9d4ff}}input,textarea,select{{width:100%;box-sizing:border-box;margin:6px 0 12px;padding:11px;border-radius:7px;border:1px solid #b9c3cf}}button{{padding:9px 15px;border-radius:7px;border:0;cursor:pointer}}table{{width:100%;border-collapse:collapse;background:#0c1b2d;border-radius:10px;overflow:hidden}}td,th{{padding:11px;text-align:left;border-bottom:1px solid #29435e;vertical-align:top}}.muted{{color:#b8c6d7}}.actions form{{display:inline-block;margin:2px}}@media(max-width:700px){{main{{padding:22px 16px}}table{{display:block;overflow-x:auto}}h1{{font-size:32px}}}}</style></head><body><header><img src="data:image/png;base64,{seal}" alt="Presidential Seal"><div><div class="brand">UNG-PRESIDENT · NATIONAL SECURITY COUNCIL</div><nav><a href="/admin">Staff Admin</a><a href="/nsc">NSC Home</a></nav></div></header><main><h1>{escape(title)}</h1>{body}</main></body></html>'''
 @app.get('/nsc',response_class=HTMLResponse)
 async def home(request:Request):
  if not auth(request):return HTMLResponse('Forbidden',403)
  with appmod.db_cursor() as cur:cur.execute('SELECT record_type,COUNT(*) n FROM nsc_records GROUP BY record_type');counts={r['record_type']:r['n'] for r in cur.fetchall()}
  cards=''.join(f'<div class="card"><h3>{escape(l)}</h3><p>{escape(d)}</p><b>{counts.get(k,0)} records</b><p><a href="/nsc/{k}">Open workspace →</a></p></div>' for l,k,d in modules)
  return HTMLResponse(page('National Security Council','<p>Presidential national-security coordination workspace.</p><div class="grid">'+cards+'</div>'))
 @app.get('/nsc/{kind}',response_class=HTMLResponse)
 async def list_records(request:Request,kind:str):
  if not auth(request):return HTMLResponse('Forbidden',403)
  valid={m[1]:m[0] for m in modules}
  if kind not in valid:return HTMLResponse('Not found',404)
  with appmod.db_cursor() as cur:cur.execute('SELECT * FROM nsc_records WHERE record_type=? ORDER BY id DESC',(kind,));rows=cur.fetchall()
  trs=''.join(f'''<tr><td>{r['id']}</td><td><strong>{escape(r['title'])}</strong><br><span class="muted">{escape(r['summary'])}</span></td><td>{escape(r['owner'])}</td><td>{escape(r['priority'])}</td><td>{escape(r['due_date'])}</td><td>{escape(r['status'])}</td><td class="actions"><form method="post" action="/nsc/{kind}/{r['id']}/status"><input type="hidden" name="status" value="in-progress"><button>Update</button></form><form method="post" action="/nsc/{kind}/{r['id']}/status"><input type="hidden" name="status" value="closed"><button>Close</button></form></td></tr>''' for r in rows)
  empty='<tr><td colspan="7" class="muted">No records yet. Create the first operational record above.</td></tr>' if not rows else ''
  body=f'''<div class="card"><h2>Create operational record</h2><form method="post"><label>Title</label><input name="title" required><label>Briefing / details</label><textarea name="summary" rows="5" required></textarea><label>Responsible office</label><input name="owner"><label>Priority</label><select name="priority"><option>normal</option><option>high</option><option>urgent</option></select><label>Due date</label><input type="date" name="due_date"><button>Create record</button></form></div><h2>Operational Records</h2><table><tr><th>ID</th><th>Record / Details</th><th>Owner</th><th>Priority</th><th>Due</th><th>Status</th><th>Actions</th></tr>{trs}{empty}</table>'''
  return HTMLResponse(page(valid[kind],body))
 @app.post('/nsc/{kind}')
 async def create(request:Request,kind:str,title:str=Form(...),summary:str=Form(...),owner:str=Form(''),priority:str=Form('normal'),due_date:str=Form('')):
  u=auth(request)
  if not u:return HTMLResponse('Forbidden',403)
  if kind not in {m[1] for m in modules}:return HTMLResponse('Not found',404)
  if priority not in {'normal','high','urgent'}:return HTMLResponse('Invalid priority',400)
  now=_now()
  with appmod.db_cursor(commit=True) as cur:
   cur.execute('INSERT INTO nsc_records(record_type,title,summary,status,classification,owner,created_at,updated_at,priority,due_date) VALUES(?,?,?,?,?,?,?,?,?,?)',(kind,title.strip(),summary.strip(),'open','restricted',owner.strip(),now,now,priority,due_date))
   rid=cur.lastrowid
  if hasattr(appmod,'log_action'): appmod.log_action(u['user_id'],u['username'],'create_nsc_record','nsc_records',rid)
  return RedirectResponse(f'/nsc/{kind}',303)
 @app.post('/nsc/{kind}/{record_id}/status')
 async def status(request:Request,kind:str,record_id:int,status:str=Form(...)):
  u=auth(request)
  if not u:return HTMLResponse('Forbidden',403)
  if status not in {'open','in-progress','closed'}:return HTMLResponse('Invalid status',400)
  with appmod.db_cursor(commit=True) as cur:cur.execute('UPDATE nsc_records SET status=?,updated_at=? WHERE id=? AND record_type=?',(status,_now(),record_id,kind))
  if hasattr(appmod,'log_action'): appmod.log_action(u['user_id'],u['username'],'update_nsc_status','nsc_records',record_id,status)
  return RedirectResponse(f'/nsc/{kind}',303)
 return app
