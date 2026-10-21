"""Production application wrapper that adds non-blocking backup export."""
from ung_president import app, db_cursor
from president_backup import start_backup_worker


@app.on_event("startup")
def start_president_backup_worker():
    start_backup_worker(db_cursor)
