import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ung_president as app


def test_revocable_session_helpers_exist():
    assert callable(app.create_persistent_session)
    assert callable(app.verify_persistent_session)
    assert callable(app.revoke_persistent_session)
