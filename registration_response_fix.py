"""Ensure registration validation failures are returned as HTML, not JSON strings."""
from fastapi.responses import HTMLResponse
import ung_president as core


def apply_registration_response_fix():
    for route in core.app.routes:
        if getattr(route, "path", None) == "/admin/register/details" and "POST" in getattr(route, "methods", set()):
            route.response_class = HTMLResponse
            return True
    raise RuntimeError("POST /admin/register/details route not found")
