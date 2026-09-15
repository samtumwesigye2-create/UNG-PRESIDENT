import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ung_president as app


def test_logout_revokes_persistent_session():
    source = inspect.getsource(app.admin_logout)
    assert 'revoke_persistent_session' in source
