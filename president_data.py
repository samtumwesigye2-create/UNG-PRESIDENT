"""Consistent SQLite backup, verified remote snapshot, and transactional migration.

Run export on the EXISTING host before redeployment. Never copy an active database
with a plain filesystem read. Credentials are environment-only and never printed.
"""
import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import sqlite3
from urllib.parse import urlparse

TABLES = ('users', 'executive_orders', 'appointments', 'honours', 'events',
          'visit_requests', 'petitions', 'state_visits', 'press_statements',
          'hr_codes', 'staff_profiles', 'audit_log')


def checksum(records):
    return hashlib.sha256(json.dumps(records, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_snapshot(payload):
    records = payload.get('records', [])
    if not isinstance(records, list) or len(records) != len(TABLES):
        raise ValueError('Incomplete table manifest')
    seen = set()
    for record in records:
        table = record.get('entity_type')
        if (table not in TABLES or table in seen or record.get('source') != 'UNG-PRESIDENT'
                or record.get('entity_id') != 'full-table' or record.get('is_deleted') is not False):
            raise ValueError('Invalid table manifest')
        rows = record.get('data', {}).get('rows')
        if not isinstance(rows, list):
            raise ValueError('Invalid table rows')
        ids = set()
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get('id'), int) or row['id'] in ids:
                raise ValueError('Invalid or duplicate record ID')
            ids.add(row['id'])
        seen.add(table)
    if not hmac.compare_digest(checksum(records), str(payload.get('checksum', ''))):
        raise ValueError('Snapshot checksum mismatch')
    return {record['entity_type']: record['data']['rows'] for record in records}


def export_sqlite(path):
    uri = Path(path).resolve().as_uri() + '?mode=ro'
    with sqlite3.connect(uri, uri=True) as source, sqlite3.connect(':memory:') as snapshot:
        source.backup(snapshot)
        snapshot.row_factory = sqlite3.Row
        if snapshot.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('SQLite integrity check failed')
        if snapshot.execute('PRAGMA foreign_key_check').fetchone():
            raise ValueError('SQLite foreign-key check failed')
        actual = {row[0] for row in snapshot.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        if actual != set(TABLES):
            raise ValueError('Unexpected source schema; refusing partial export')
        records = [{'source': 'UNG-PRESIDENT', 'entity_type': table, 'entity_id': 'full-table',
                    'data': {'rows': [dict(row) for row in snapshot.execute(f'SELECT * FROM "{table}" ORDER BY id')]},
                    'is_deleted': False, 'source_updated_at': None} for table in TABLES]
    result = {'records': records, 'checksum': checksum(records)}
    validate_snapshot(result)
    return result


def upload_snapshot(payload, base_url, sync_token, restore_token):
    import httpx
    validate_snapshot(payload)
    parsed = urlparse(base_url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Backup destination must be HTTPS without URL credentials')
    if not sync_token or not restore_token:
        raise ValueError('Both backup sync and restore verification tokens are required')
    with httpx.Client(timeout=120, follow_redirects=False) as client:
        response = client.post(base_url.rstrip('/') + '/president/snapshot', json=payload,
                               headers={'x-backup-token': sync_token})
        response.raise_for_status()
        receipt = response.json()
        saved = client.get(base_url.rstrip('/') + '/snapshot/' + str(int(receipt['id'])),
                           headers={'x-backup-restore-token': restore_token})
        saved.raise_for_status()
        stored = saved.json()
        verified = {'records': stored['data'], 'checksum': stored['checksum']}
        validate_snapshot(verified)
        if verified != payload or stored.get('integrity') != 'ok':
            raise ValueError('Remote backup readback mismatch')
        return {'id': receipt['id'], 'checksum': payload['checksum'], 'verified': True}


def migrate_postgres(payload, database_url, *, commit=False):
    import psycopg
    from psycopg import sql
    from psycopg.rows import dict_row
    import ung_president as app
    tables = validate_snapshot(payload)
    if urlparse(database_url).scheme not in ('postgres', 'postgresql'):
        raise ValueError('A PostgreSQL destination is required')
    schema = app.SCHEMA.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'BIGSERIAL PRIMARY KEY')
    schema = schema.replace("DEFAULT (datetime('now'))", 'DEFAULT CURRENT_TIMESTAMP')
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_advisory_xact_lock(70915001)')
            for statement in schema.split(';'):
                if statement.strip():
                    cursor.execute(statement)
            # Lock before checking emptiness; concurrent application writes cannot
            # race the empty-database guard.
            cursor.execute(sql.SQL('LOCK TABLE {} IN ACCESS EXCLUSIVE MODE').format(
                sql.SQL(',').join(sql.Identifier(table) for table in TABLES)))
            for table in TABLES:
                cursor.execute(sql.SQL('SELECT COUNT(*) AS n FROM {}').format(sql.Identifier(table)))
                if cursor.fetchone()['n']:
                    raise ValueError('Destination is not empty; refusing overwrite')
            for table in TABLES:
                for row in tables[table]:
                    columns = list(row)
                    cursor.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(
                        sql.Identifier(table), sql.SQL(',').join(map(sql.Identifier, columns)),
                        sql.SQL(',').join(sql.Placeholder() for _ in columns)), list(row.values()))
                cursor.execute(sql.SQL('SELECT * FROM {} ORDER BY id').format(sql.Identifier(table)))
                if cursor.fetchall() != sorted(tables[table], key=lambda row: row['id']):
                    raise ValueError('Destination readback mismatch: ' + table)
                cursor.execute("SELECT setval(pg_get_serial_sequence(%s, 'id'), %s, %s)",
                               (table, max((row['id'] for row in tables[table]), default=1), bool(tables[table])))
            counts = {table: len(tables[table]) for table in TABLES}
            if not commit:
                connection.rollback()
    return {'committed': commit, 'counts': counts, 'checksum': payload['checksum']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    export = sub.add_parser('export')
    export.add_argument('--sqlite', required=True)
    export.add_argument('--output', required=True)
    upload = sub.add_parser('upload')
    upload.add_argument('--snapshot', required=True)
    migrate = sub.add_parser('migrate')
    migrate.add_argument('--snapshot', required=True)
    migrate.add_argument('--commit', action='store_true')
    args = parser.parse_args()
    if args.command == 'export':
        payload = export_sqlite(args.sqlite)
        fd = os.open(args.output, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, 'w') as target:
            json.dump(payload, target)
        result = {'checksum': payload['checksum'], 'tables': len(payload['records'])}
    else:
        with open(args.snapshot) as source:
            payload = json.load(source)
        if args.command == 'upload':
            result = upload_snapshot(payload, os.environ['BACKUP_URL'], os.environ['BACKUP_SYNC_TOKEN'], os.environ['BACKUP_RESTORE_TOKEN'])
        else:
            result = migrate_postgres(payload, os.environ['DATABASE_URL'], commit=args.commit)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
