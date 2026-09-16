"""Ensure registration validation failures are returned as HTML, not JSON strings."""
from fastapi.responses import HTMLResponse
import ung_president as core


def apply_registration_response_fix():
    for index, route in enumerate(core.app.routes):
        if getattr(route, "path", None) == "/admin/register/details" and "POST" in getattr(route, "methods", set()):
            endpoint = route.endpoint
            core.app.routes.pop(index)
            core.app.add_api_route(
                "/admin/register/details",
                endpoint,
                methods=["POST"],
                response_class=HTMLResponse,
            )
            return True
    raise RuntimeError("POST /admin/register/details route not found")
