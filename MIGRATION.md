# UNG-PRESIDENT backup and migration

The live SQLite file must be exported **before any application redeployment**.
Run the export command on the existing container host using the supplied
`president_data.py` (standard-library-only export). A binary file viewer that
truncates output is not a backup mechanism.

1. Quiesce application writes for the final cutover. Keep the old instance and
   signing secret available for rollback. Do not restart it to add a backup tool.
2. `python president_data.py export --sqlite /app/ung_president.db --output /secure/president-snapshot.json`
3. Supply `BACKUP_URL`, `BACKUP_SYNC_TOKEN`, and `BACKUP_RESTORE_TOKEN` via the
   authenticated environment. Run `python president_data.py upload --snapshot /secure/president-snapshot.json`.
   This requires the backup service's new `/president/snapshot` endpoint. Upload
   succeeds only after reading the stored snapshot back and checking all content.
4. With `DATABASE_URL` pointing to the new empty PostgreSQL database, run
   `python president_data.py migrate --snapshot /secure/president-snapshot.json`.
   This performs schema creation, insertions and full readback inside a transaction
   that is rolled back by default. Record counts and checksum are printed; records
   and credentials are not.
5. Repeat with `--commit` only after remote backup verification and the dry run pass.
   Nonempty destinations are rejected. Existing IDs, password hashes, salts and
   audit records are preserved. Keep the existing `UNG_PRESIDENT_SECRET` unchanged.
6. Switch the web service to PostgreSQL and deploy the verified application. Test
   the old administrator login, petitions and privileged access. Keep the original
   snapshot until the new service and backup recovery have been accepted.

Backup snapshots include sensitive account and citizen records. Export files use
mode 0600 and refuse to overwrite existing files. Snapshot download requires the
backup restore credential. Do not publish snapshots, passwords or connection URLs.

This tool is a cutover facility, not scheduled continuous protection. Ongoing
PostgreSQL backups and retention must be configured before production acceptance.

Validation: local tests exercise SQLite export, integrity checks and missing-source
rejection. GitHub Actions uses an isolated PostgreSQL 18 service for migration,
existing-login verification, sequence continuation and rollback tests. These tests
do not establish that a production backup has been captured.
