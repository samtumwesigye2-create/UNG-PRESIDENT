import asyncio

import ung_president as app


def test_export_backup_records_reads_president_tables(tmp_path):
    import president_backup

    app.DATABASE_URL = ""
    app.DB_PATH = str(tmp_path / "president-backup.db")
    app.init_db()
    hashed, salt = app.hash_password("Strong-password-123")
    with app.db_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO users(username,password_hash,salt,role,full_name) VALUES(?,?,?,?,?)",
            ("backup-user", hashed, salt, "admin", "Backup User"),
        )

    exported = president_backup.export_backup_records(app.db_cursor)

    assert set(exported) == set(president_backup.BACKUP_TABLES)
    assert any(row["username"] == "backup-user" for row in exported["users"])
    assert all("id" in row for rows in exported.values() for row in rows)


def test_backup_sync_is_safe_noop_without_configuration(monkeypatch, tmp_path):
    import president_backup

    app.DATABASE_URL = ""
    app.DB_PATH = str(tmp_path / "president-backup.db")
    app.init_db()
    monkeypatch.delenv("BACKUP_SERVICE_URL", raising=False)
    monkeypatch.delenv("BACKUP_SYNC_TOKEN", raising=False)

    result = asyncio.run(president_backup.sync_backup_snapshot(app.db_cursor))

    assert result == {"status": "disabled", "tables": 0, "records": 0}
