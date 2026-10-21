"""Read-only UNG-PRESIDENT export into the existing UGA Backup Service."""
import asyncio
import os
import threading
import time
from datetime import date, datetime

import httpx

SOURCE_NAME = "UNG-PRESIDENT"
BACKUP_TABLES = (
    "users",
    "executive_orders",
    "appointments",
    "honours",
    "events",
    "visit_requests",
    "petitions",
    "state_visits",
    "press_statements",
    "hr_codes",
    "staff_profiles",
    "audit_log",
)
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


def _row_to_dict(row):
    return _json_safe(dict(row))


def export_backup_records(cursor_factory):
    """Return a read-only, JSON-safe export of every persistent PRESIDENT table."""
    exported = {}
    for table in BACKUP_TABLES:
        with cursor_factory() as cur:
            cur.execute(f"SELECT * FROM {table} ORDER BY id")
            exported[table] = [_row_to_dict(row) for row in cur.fetchall()]
    return exported


async def sync_backup_snapshot(cursor_factory):
    """Push a full read-only mirror to UGA Backup Service.

    Missing configuration is intentionally a safe no-op so backup outages do not
    prevent the presidential application from serving requests.
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
                json={
                    "source": SOURCE_NAME,
                    "entity_type": table,
                    "records": records,
                    "replace": True,
                },
                headers={"x-backup-token": backup_token},
            )
            response.raise_for_status()
            table_count += 1
            record_count += len(records)
    return {"status": "ok", "tables": table_count, "records": record_count}


def start_backup_worker(cursor_factory):
    """Start one daemon worker that refreshes the backup mirror hourly by default."""
    if not os.environ.get("BACKUP_SERVICE_URL") or not os.environ.get("BACKUP_SYNC_TOKEN"):
        return False

    def worker():
        time.sleep(15)
        while True:
            try:
                asyncio.run(sync_backup_snapshot(cursor_factory))
            except Exception as exc:
                print(f"UNG-PRESIDENT backup sync failed: {type(exc).__name__}")
            time.sleep(BACKUP_EXPORT_INTERVAL_SECONDS)

    threading.Thread(target=worker, name="ung-president-backup", daemon=True).start()
    return True
