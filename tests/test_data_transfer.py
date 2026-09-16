import hashlib
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
import ung_president as app


def test_export_is_complete_and_preserves_account_material(tmp_path, monkeypatch):
    import president_data as transfer
    monkeypatch.setattr(app, 'DB_PATH', str(tmp_path / 'source.db'))
    monkeypatch.setattr(app, 'DATABASE_URL', '')
    app.init_db()
    with app.db_cursor(commit=True) as cur:
        cur.execute('INSERT INTO users(username,password_hash,salt,role,full_name) VALUES(?,?,?,?,?)',
                    ('example', 'preserve-hash', 'preserve-salt', 'staff', 'Example'))
    result = transfer.export_sqlite(app.DB_PATH)
    assert len(result['records']) == 12
    users = next(r['data']['rows'] for r in result['records'] if r['entity_type'] == 'users')
    assert users[0]['password_hash'] == 'preserve-hash'
    assert users[0]['salt'] == 'preserve-salt'
    assert result['checksum'] == hashlib.sha256(json.dumps(result['records'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    transfer.validate_snapshot(result)
    result['records'][0]['data']['rows'][0]['salt'] = 'tampered'
    with pytest.raises(ValueError, match='checksum'):
        transfer.validate_snapshot(result)


def test_missing_source_is_not_created(tmp_path):
    import president_data as transfer
    path = tmp_path / 'absent.db'
    with pytest.raises((ValueError, sqlite3.OperationalError)):
        transfer.export_sqlite(str(path))
    assert not path.exists()


def test_partial_database_rejected(tmp_path):
    import president_data as transfer
    path = tmp_path / 'partial.db'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE users(id INTEGER PRIMARY KEY)')
    with pytest.raises(ValueError, match='schema'):
        transfer.export_sqlite(str(path))
