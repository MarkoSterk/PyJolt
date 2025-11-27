"""
Main admin dashboard controller module.
Handles login and static files
"""
# pylint: disable=W0719,W0212
from __future__ import annotations

import mimetypes
import os
from typing import TYPE_CHECKING

from werkzeug.security import safe_join

from ..controller import get
from ..exceptions.http_exceptions import StaticAssetNotFound
from ..request import Request
from ..response import Response
from ..utilities import get_file, get_range_file
from .common_controller import CommonAdminController

if TYPE_CHECKING:
    from .admin_dashboard import AdminDashboard

class AdminController(CommonAdminController):
    """Admin dashboard controller."""

    _dashboard: "AdminDashboard"

    @get("/login")
    async def login(self, req: Request) -> Response:
        """Login route for dashboard"""
        return await req.res.html(
            "/__admin_templates/login.html",
            {"configs": self.dashboard.configs}
        )
    
    @get("/test")
    async def test(self, req: Request) -> Response:
        return await req.res.html("/__admin_templates/admin_index.html")

    #STATIC files for dashboard
    @get("/static/<path:filename>")
    async def static(self, req: Request, filename: str) -> Response:
        """Serves static assets for the dashboard"""
        file_path = None
        candidate = safe_join(self.dashboard.root_path, "static", filename)
        if candidate and os.path.exists(candidate):
            file_path = candidate
        if not file_path:
            raise StaticAssetNotFound()

        # checks/guesses mimetype
        guessed, _ = mimetypes.guess_type(file_path)
        content_type = guessed or "application/octet-stream"

        # Checks range header and returns range if header is present
        range_header = req.headers.get("range")
        if not range_header:
            status, headers, body = await get_file(file_path, content_type=content_type)
            headers["Accept-Ranges"] = "bytes"
            return req.res.send_file(body, headers).status(status)

        return await get_range_file(req.res, file_path, range_header, content_type)
