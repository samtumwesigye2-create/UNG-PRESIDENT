import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ung_president as app


def test_schema_defines_revocable_sessions():
    schema = app.SCHEMA.lower()
    assert 'create table if not exists sessions' in schema
    assert 'token_hash' in schema
    assert 'expires_at' in schema
    assert 'revoked_at' in schema
