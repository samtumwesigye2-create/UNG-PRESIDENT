import sys
from pathlib import Path
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ung_president as app
import president_un_affairs

def client(tmp_path):
    app.DB_PATH=str(tmp_path/'un.db'); app._rate_buckets.clear(); app.init_db(); president_un_affairs.apply_un_affairs(app); return TestClient(app.app)

def login(c):
    hashed,salt=app.hash_password('Strong-password-123')
    with app.db_cursor(commit=True) as cur: cur.execute('INSERT INTO users(username,password_hash,salt,role,full_name) VALUES(?,?,?,?,?)',('un-admin',hashed,salt,'admin','UN Admin'))
    assert c.post('/admin/login',data={'username':'un-admin','password':'Strong-password-123'},follow_redirects=False).status_code==303

def test_un_affairs_uses_uganda_language_and_no_us_veto(tmp_path):
    with client(tmp_path) as c:
        login(c); r=c.get('/admin/un-affairs'); assert r.status_code==200
        for text in ['Uganda Mission to the United Nations','Uganda Representation & Negotiations','Leadership & NSC Briefings','Diplomatic Engagement','Resolutions & Voting','Multilateral Policy']: assert text in r.text
        assert 'U.S.' not in r.text and 'United States' not in r.text and 'veto' not in r.text.lower()

def test_create_un_record_and_nsc_linkage(tmp_path):
    with client(tmp_path) as c:
        login(c)
        r=c.post('/admin/un-affairs',data={'workstream':'Resolutions & Voting','title':'Resolution position','un_body':'General Assembly','uganda_position':'Position under review','voting_position':'Abstain','nsc_relevance':'1','owner':'Uganda UN Mission'},follow_redirects=False)
        assert r.status_code==303
        page=c.get('/admin/un-affairs'); assert 'Resolution position' in page.text and 'Abstain' in page.text and 'Yes' in page.text
