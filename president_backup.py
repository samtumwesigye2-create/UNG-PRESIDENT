"""Hourly read-only copy of the UNG-PRESIDENT database to the UGA Backup Service.

The worker only starts when both BACKUP_SERVICE_URL and BACKUP_SYNC_TOKEN are
set, so a missing configuration or a backup-service outage never affects the
site itself. Every table is discovered from the live database, so tables added
by later modules are included automatically.

Short-lived login material (active sessions and one-time reset tokens) is not
copied: it is useless after a restore and only widens what a leaked backup
would expose.
"""
import asyncio
import os
import threading
import time
from datetime import date, datetime

import httpx

SOURCE_NAME = "UNG-PRESIDENT"
EXCLUDED_TABLES = frozenset({
    "password_reset_tokens",
    "executive_sessions",
    "executive_leadership_sessions",
})
BACKUP_EXPORT_INTERVAL_SECONDS = max(
    3600, int(os.environ.get("BACKUP_EXPORT_INTERVAL_SECONDS", "3600"))
)


def _json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


def backup_tables(cursor_factory):
    """Every user table in the database, minus short-lived login material."""
    with cursor_factory() as cur:
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        names = [row["name"] for row in cur.fetchall()]
    return [n for n in names if n not in EXCLUDED_TABLES]


def export_backup_records(cursor_factory):
    """Return a read-only, JSON-safe export of every backed-up table."""
    exported = {}
    for table in backup_tables(cursor_factory):
        with cursor_factory() as cur:
            # Table names come from sqlite_master, never from user input.
            cur.execute(f'SELECT * FROM "{table}" ORDER BY rowid')
            exported[table] = [_json_safe(dict(row)) for row in cur.fetchall()]
    return exported


async def sync_backup_snapshot(cursor_factory):
    """Push a full read-only mirror to the UGA Backup Service.

    Missing configuration is a safe no-op so backup problems never stop the site.
    """
    backup_url = os.environ.get("BACKUP_SERVICE_URL", "").strip().rstrip("/")
    backup_token = os.environ.get("BACKUP_SYNC_TOKEN", "").strip()
    if not backup_url or not backup_token:
        return {"status": "disabled", "tables": 0, "records": 0}

    exported = export_backup_records(cursor_factory)
    table_count = 0
    record_count = 0
    async with httpx.AsyncClient(timeout=30) as client:
        for table, records in exported.items():
            response = await client.post(
                f"{backup_url}/sync/bulk",
                json={"source": SOURCE_NAME, "entity_type": table, "records": records, "replace": True},
                headers={"x-backup-token": backup_token},
            )
            response.raise_for_status()
            table_count += 1
            record_count += len(records)
    return {"status": "ok", "tables": table_count, "records": record_count}


def start_backup_worker(cursor_factory):
    """Start one background thread that refreshes the backup mirror (hourly by default)."""
    if not os.environ.get("BACKUP_SERVICE_URL") or not os.environ.get("BACKUP_SYNC_TOKEN"):
        return False

    def worker():
        time.sleep(15)
        while True:
            try:
                result = asyncio.run(sync_backup_snapshot(cursor_factory))
                print(f"UNG-PRESIDENT backup sync: {result['tables']} tables, {result['records']} records", flush=True)
            except Exception as exc:
                # Never print the exception text: it can contain the backup URL or token.
                print(f"UNG-PRESIDENT backup sync failed: {type(exc).__name__}", flush=True)
            time.sleep(BACKUP_EXPORT_INTERVAL_SECONDS)

    threading.Thread(target=worker, name="ung-president-backup", daemon=True).start()
    return True
