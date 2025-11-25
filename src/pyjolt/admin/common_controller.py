"""Common controller methods"""
# pylint: disable=W0719,W0212
from __future__ import annotations

from typing import TYPE_CHECKING
from ..exceptions.http_exceptions import BaseHttpException
from ..http_statuses import HttpStatus
from ..request import Request
from ..response import Response
from .templates.denied_entry import DENIED_ENTRY
from ..controller import Controller

if TYPE_CHECKING:
    from .admin_dashboard import AdminDashboard

class AdminEnterError(BaseHttpException):
    """Error for when a user does not have permission to enter the dashboard"""
    def __init__(self, user):
        super().__init__("User doesn't have access to admin dashboard",
                         HttpStatus.UNAUTHORIZED, "error", user)

class CommonAdminController(Controller):
    """Admin dashboard controller."""

    _dashboard: "AdminDashboard"

    async def cant_enter_response(self, req: Request) -> Response:
        """Response for when a user cannot enter the dashboard"""
        return (await req.res.html_from_string(
            DENIED_ENTRY
        )).status(HttpStatus.UNAUTHORIZED)

    async def can_enter(self, req: Request) -> bool:
        """
        Method for checking permission to enter
        admin dashboard
        """
        has_permission: bool = False
        has_permission = await self.dashboard.has_enter_permission(req)
        if not has_permission:
            raise AdminEnterError(req.user)
        return has_permission

    @property
    def dashboard(self) -> "AdminDashboard":
        return self._dashboard
