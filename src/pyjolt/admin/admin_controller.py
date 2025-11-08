"""Admin controller module."""
from enum import StrEnum
from typing import Any, Optional, cast, Type, TYPE_CHECKING

from ..database.sql.base_protocol import DeclarativeBaseModel
from .templates.login import LOGIN_TEMPLATE
from ..controller import (Controller, get, post,
                          put, delete)
from ..auth.authentication_mw import login_required
from ..request import Request
from ..response import Response
from ..http_statuses import HttpStatus
from ..exceptions.http_exceptions import BaseHttpException

if TYPE_CHECKING:
    from .admin_dashboard import AdminDashboard

class UnknownModelError(BaseHttpException):
    """Unknown model for admin dashboard"""

    def __init__(self, db_name: str, model_name: str):
        """Init method for exception"""
        super().__init__(f"Model {model_name} in database {db_name} does not exist",
                         HttpStatus.NOT_FOUND, "error", {"db_name": db_name,
                                                         "model_name": model_name})

class AdminPermissionError(BaseHttpException):
    """Unknown model for admin dashboard"""

    def __init__(self, user: Any):
        """Init method for exception"""
        super().__init__("User doesn't have permission for this action",
                         HttpStatus.NOT_FOUND, "error", user)


class PermissionType(StrEnum):
    CAN_VIEW = "view"
    CAN_CREATE = "create"
    CAN_EDIT = "edit"
    CAN_DELETE = "delete"

class AdminController(Controller):
    """Admin dashboard controller."""

    _dashboard: "AdminDashboard"

    @get("/login")
    async def login(self, req: Request) -> Response:
        """Login route for dashboard"""
        #pylint: disable-next=C0103
        URL_FOR_FOR_LOGIN: str = cast(dict[str, str],
                                  self.app.get_conf("ADMIN_DASHBOARD"))["URL_FOR_FOR_LOGIN"]

        return await req.res.html_from_string(
            LOGIN_TEMPLATE,
            {"URL_FOR_FOR_LOGIN": URL_FOR_FOR_LOGIN}
        )

    @get("/logout")
    @login_required
    async def logout(self, req: Request) -> Response:
        """Logout from dashboard"""
        return req.res.redirect(self.app.url_for("AuthController.logout"))

    @get("/")
    @login_required
    async def index(self, req: Request) -> Response:
        """Get admin dashboard data."""
        return await req.res.html_from_string("<h1>Admin Dashboard</h1>")

    @get("/data/database/<string:db_name>/model/<string:model_name>")
    @login_required
    async def model_table(self, req: Request, db_name: str,
                                    model_name: str) -> Response:
        """Handle model table operations."""
        model = await self.check_permission(PermissionType.CAN_VIEW, req, db_name, model_name)
        print("Viewing model table: ", model.__name__)
        return await req.res.html_from_string(
            "<h1>Model Table</h1><p>{{model_name}}</p>",
            {"model_name": model_name}
        )

    @get("/data/database/<string:db_name>/model/<string:model_name>/<int:record_id>")
    @login_required
    async def get_model_record(self, req: Request, db_name: str,
                                    model_name: str, record_id: int) -> Response:
        """Get a specific model record."""
        model = await self.check_permission(PermissionType.CAN_VIEW, req, db_name, model_name)
        print("View one model: ", model.__name__)
        return await req.res.html_from_string(
            "<h1>Model Record</h1><p>{{model_name}} - {{record_id}}</p>",
            {"model_name": model_name, "record_id": record_id}
        )

    @delete("/data/database/<string:db_name>/model/<string:model_name>/<int:record_id>")
    @login_required
    async def delete_model_record(self, req: Request, db_name: str,
                                    model_name: str, record_id: int) -> Response:
        """Delete a specific model record."""
        model = await self.check_permission(PermissionType.CAN_DELETE, req, db_name, model_name)
        print("Deleting model: ", model.__name__)
        return await req.res.html_from_string(
            "<h1>Deleted Record</h1><p>{{model_name}} - {{record_id}}</p>",
            {"model_name": model_name, "record_id": record_id}
        )

    @put("/data/database/<string:db_name>/model/<string:model_name>/<int:record_id>")
    @login_required
    async def put_model_record(self, req: Request, db_name: str,
                                    model_name: str, record_id: int) -> Response:
        """Patch a specific model record."""
        model = await self.check_permission(PermissionType.CAN_EDIT, req, db_name, model_name)
        print("Editing model: ", model.__name__)
        return await req.res.html_from_string(
            "<h1>Patched Record</h1><p>{{model_name}} - {{record_id}}</p>",
            {"model_name": model_name, "record_id": record_id}
        )

    @post("/data/database/<string:db_name>/model/<string:model_name>")
    @login_required
    async def create_model_record(self, req: Request, db_name: str, 
                                    model_name: str) -> Response:
        """Create a new model record."""
        model = await self.check_permission(PermissionType.CAN_CREATE, req, db_name, model_name)
        print("Creating model: ", model.__name__)
        return await req.res.html_from_string(
            "<h1>Created Record</h1><p>{{model_name}}</p>",
            {model_name: model_name}
        )

    async def check_permission(self, perm_type: PermissionType,
                               req: Request,
                               db_name: str,
                               model_name: str) -> Type[DeclarativeBaseModel]:
        """Method for cheking permissions"""
        model: Optional[Type[DeclarativeBaseModel]] = self.dashboard.get_model(
            db_name, model_name
        )
        if model is None:
            raise UnknownModelError(db_name, model_name)
        has_permission: bool = False
        if perm_type == PermissionType.CAN_VIEW:
            has_permission = await self.dashboard.has_view_permission(req, model)
        elif perm_type == PermissionType.CAN_CREATE:
            has_permission = await self.dashboard.has_create_permission(req, model)
        elif perm_type == PermissionType.CAN_EDIT:
            has_permission = await self.dashboard.has_edit_permission(req, model)
        else:
            has_permission = await self.dashboard.has_delete_permission(req, model)

        if not has_permission:
            raise AdminPermissionError("User does not have permission "
                                          f"to {perm_type} model data.")
        return model

    @property
    def dashboard(self) -> "AdminDashboard":
        return self._dashboard
