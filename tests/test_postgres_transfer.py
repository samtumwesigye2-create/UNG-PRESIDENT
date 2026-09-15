"""Run with TEST_POSTGRES_URL against an isolated disposable PostgreSQL server."""
import os
import uuid
import pytest
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
import ung_president as app
import president_data as transfer
from fastapi.testclient import TestClient


@pytest.fixture
def destination():
    url = os.environ.get('TEST_POSTGRES_URL')
    if not url:
        pytest.skip('TEST_POSTGRES_URL not configured')
    schema = 'acceptance_' + uuid.uuid4().hex
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    scoped = make_conninfo(url, options=f'-c search_path={schema}')
    # Preserve a URL for the migration's backend guard and psycopg options.
    from urllib.parse import quote
    scoped_url = url + ('&' if '?' in url else '?') + 'options=' + quote(f'-c search_path={schema}')
    yield scoped_url
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


@pytest.fixture
def snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr(app, 'DATABASE_URL', '')
    monkeypatch.setattr(app, 'DB_PATH', str(tmp_path / 'source.db'))
    app.init_db()
    hashed, salt = app.hash_password('Strong-password-123')
    with app.db_cursor(commit=True) as cur:
        cur.execute('INSERT INTO users(id,username,password_hash,salt,role,full_name) VALUES(?,?,?,?,?,?)',
                    (21, 'existing', hashed, salt, 'admin', 'Existing Account'))
        cur.execute('INSERT INTO petitions(petitioner_name,email,subject,message,handled_by) VALUES(?,?,?,?,?)',
                    ('Example', 'example@example.com', 'Existing petition', 'Preserve this record', 21))
    return transfer.export_sqlite(app.DB_PATH)


def test_postgres_migration_and_existing_login(destination, snapshot, monkeypatch):
    result = transfer.migrate_postgres(snapshot, destination, commit=True)
    assert result['counts']['users'] == 1
    assert result['counts']['petitions'] == 1
    monkeypatch.setattr(app, 'DATABASE_URL', destination)
    with TestClient(app.app) as client:
        assert client.get('/').status_code == 200
        response = client.post('/admin/login', data={'username': 'existing', 'password': 'Strong-password-123'}, follow_redirects=False)
        assert response.status_code == 303
        assert client.get('/admin/petitions').status_code == 200
        assert 'Preserve this record' in client.get('/admin/petitions').text
    with app.db_cursor(commit=True) as cur:
        cur.execute('INSERT INTO users(username,password_hash,salt,role,full_name) VALUES(?,?,?,?,?)',
                    ('next', 'hash', 'salt', 'staff', 'Next'))
        cur.execute('SELECT id FROM users WHERE username=?', ('next',))
        assert cur.fetchone()['id'] == 22
    with pytest.raises(ValueError, match='not empty'):
        transfer.migrate_postgres(snapshot, destination, commit=True)


def test_dry_run_rolls_back(destination, snapshot):
    assert transfer.migrate_postgres(snapshot, destination)['committed'] is False
    with psycopg.connect(destination) as connection:
        assert connection.execute("SELECT to_regclass('users')").fetchone()[0] is None


def test_invalid_foreign_key_rolls_back_every_table(destination, snapshot):
    petitions = next(r for r in snapshot['records'] if r['entity_type'] == 'petitions')
    petitions['data']['rows'][0]['handled_by'] = 999
    snapshot['checksum'] = transfer.checksum(snapshot['records'])
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        transfer.migrate_postgres(snapshot, destination, commit=True)
    with psycopg.connect(destination) as connection:
        assert connection.execute("SELECT to_regclass('users')").fetchone()[0] is None
