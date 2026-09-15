import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ung_president as app


def test_persistent_session_uses_random_opaque_token():
    source = inspect.getsource(app.create_persistent_session)
    assert 'token_urlsafe' in source or 'token_hex' in source
    assert 'token_hash' in source
