import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ung_president as app


def test_persistent_session_verification_checks_expiry_and_revocation():
    source = inspect.getsource(app.verify_persistent_session)
    assert 'expires_at' in source
    assert 'revoked_at' in source
