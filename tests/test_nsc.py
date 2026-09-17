import sys
from pathlib import Path
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ung_president as app
import president_nsc

def setup_client(tmp_path):
 app.DB_PATH=str(tmp_path/'nsc-test.db');app._rate_buckets.clear();app.init_db();president_nsc.apply_nsc(app);return TestClient(app.app)
def login(client,role='admin'):
 hashed,salt=app.hash_password('Strong-password-123')
 with app.db_cursor(commit=True) as cur:cur.execute('INSERT INTO users(username,password_hash,salt,role,full_name) VALUES(?,?,?,?,?)',('nsc-user',hashed,salt,role,'NSC User'))
 assert client.post('/admin/login',data={'username':'nsc-user','password':'Strong-password-123'},follow_redirects=False).status_code==303
def test_nsc_requires_authorization(tmp_path):
 with setup_client(tmp_path) as client:assert client.get('/nsc').status_code==403
def test_admin_can_open_nsc_and_modules(tmp_path):
 with setup_client(tmp_path) as client:
  login(client);r=client.get('/nsc');assert r.status_code==200
  assert 'Presidential Seal' in r.text
  for label in ['Presidential Briefings','NSC Meetings & Agendas','Interagency Coordination','Presidential Directives','Situation Room','Analysis & Policy Options','Leader & Summit Preparation','Security Communications']:assert label in r.text
def test_nsc_record_creation_and_actions(tmp_path):
 with setup_client(tmp_path) as client:
  login(client);r=client.post('/nsc/briefing',data={'title':'Morning brief','summary':'Executive briefing','owner':'NSC Secretariat','priority':'high','due_date':'2026-09-18','status':'open'},follow_redirects=False);assert r.status_code==303
  page=client.get('/nsc/briefing');assert 'Morning brief' in page.text and 'Executive briefing' in page.text and 'high' in page.text and '2026-09-18' in page.text
  assert 'Update' in page.text and 'Close' in page.text
  with app.db_cursor() as cur:
   cur.execute("SELECT id FROM nsc_records WHERE title='Morning brief'"); rid=cur.fetchone()['id']
  assert client.post(f'/nsc/briefing/{rid}/status',data={'status':'closed'},follow_redirects=False).status_code==303
  assert 'closed' in client.get('/nsc/briefing').text
