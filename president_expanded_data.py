"""Additive persistent schema for expanded UNG-PRESIDENT modules."""

import ung_president as core


SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS citizens_abroad (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        country TEXT NOT NULL,
        city TEXT,
        passport_number TEXT,
        phone TEXT,
        email TEXT,
        emergency_contact TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS travel_advisories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country TEXT NOT NULL,
        level TEXT NOT NULL,
        title TEXT NOT NULL,
        summary TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_by INTEGER,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS emergency_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        severity TEXT NOT NULL,
        audience TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_by INTEGER,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS diplomatic_missions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mission_name TEXT NOT NULL,
        country TEXT NOT NULL,
        city TEXT,
        mission_type TEXT NOT NULL DEFAULT 'embassy',
        phone TEXT,
        email TEXT,
        address TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS consular_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        citizen_name TEXT NOT NULL,
        country TEXT NOT NULL,
        case_type TEXT NOT NULL,
        priority TEXT NOT NULL DEFAULT 'normal',
        status TEXT NOT NULL DEFAULT 'open',
        assigned_to INTEGER,
        notes TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS media_accreditations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        applicant_name TEXT NOT NULL,
        organization TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        event_name TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        reviewed_by INTEGER,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS document_attestations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        applicant_name TEXT NOT NULL,
        document_type TEXT NOT NULL,
        reference_number TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        notes TEXT,
        reviewed_by INTEGER,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS treaty_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        partner TEXT,
        signed_date TEXT,
        document_reference TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        notes TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS approval_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        subject_type TEXT NOT NULL,
        subject_id INTEGER,
        payload TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        initiator_user_id INTEGER NOT NULL,
        approver_user_id INTEGER,
        decision_note TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        decided_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS biometric_enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        modality TEXT NOT NULL,
        device_id TEXT,
        external_reference TEXT,
        template_hash TEXT,
        status TEXT NOT NULL DEFAULT 'enrolled',
        enrolled_by INTEGER,
        enrolled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, modality)
    )
    """,
)


def init_expanded_schema():
    """Create expanded module tables without altering existing production data."""
    core.init_db()
    with core.db_cursor(commit=True) as cur:
        for statement in SCHEMA:
            cur.execute(statement)
