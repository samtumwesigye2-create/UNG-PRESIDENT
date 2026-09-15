import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ung_president as app


def test_login_creates_persistent_session():
    source = inspect.getsource(app.login)
    assert 'create_persistent_session' in source


def test_current_user_verifies_persistent_session():
    source = inspect.getsource(app.get_current_user)
    assert 'verify_persistent_session' in source
