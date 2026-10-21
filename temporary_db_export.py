"""Temporary production database export route for migration verification.

Remove this module and its bootstrap import immediately after the verified
snapshot has been retrieved.
"""
import hmac
import os

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse

import ung_president as core


def register_export_route():
    expected = os.environ.get("UNG_PRESIDENT_EXPORT_TOKEN")
    if not expected:
        raise RuntimeError("UNG_PRESIDENT_EXPORT_TOKEN must be set while DB export route is enabled")

    @core.app.get("/admin/export-db", include_in_schema=False)
    def export_db(request: Request, token: str = ""):
        user = core.get_current_user(request)
        supplied = token or request.headers.get("X-UNG-EXPORT-TOKEN", "")
        if not hmac.compare_digest(supplied, expected):
            raise HTTPException(status_code=404, detail="Not found")
        if user and user.get("role") not in ("admin", "president"):
            raise HTTPException(status_code=403, detail="Not authorized")
        if not os.path.isfile(core.DB_PATH):
            raise HTTPException(status_code=404, detail="Database not found")
        return FileResponse(
            core.DB_PATH,
            media_type="application/vnd.sqlite3",
            filename="ung_president-production.sqlite3",
        )
