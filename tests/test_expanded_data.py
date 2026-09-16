import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ung_president as core


EXPANDED_TABLES = {
    "citizens_abroad",
    "travel_advisories",
    "emergency_alerts",
    "diplomatic_missions",
    "consular_cases",
    "media_accreditations",
    "document_attestations",
    "treaty_archive",
    "approval_requests",
    "biometric_enrollments",
}


def test_expanded_schema_is_additive(tmp_path):
    core.DB_PATH = str(tmp_path / "expanded-schema.db")
    core.init_db()

    import president_expanded_data
    president_expanded_data.init_expanded_schema()

    with sqlite3.connect(core.DB_PATH) as conn:
        names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}

    assert "users" in names
    assert "hr_codes" in names
    assert EXPANDED_TABLES <= names
