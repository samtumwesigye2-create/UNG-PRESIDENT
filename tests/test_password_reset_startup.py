import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ung_president as app


def test_password_reset_schema_bootstraps_empty_database(tmp_path):
    app.DB_PATH = str(tmp_path / "fresh-production.db")
    with contextlib.redirect_stdout(io.StringIO()):
        import password_reset as reset
        reset._ensure_schema()
    with app.db_cursor() as cur:
        tables = {row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        user_cols = {row[1] for row in cur.execute("PRAGMA table_info(users)").fetchall()}
    assert "users" in tables
    assert "password_reset_tokens" in tables
    assert "password_changed_at" in user_cols
