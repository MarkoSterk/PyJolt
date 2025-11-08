"""Admin controller module."""
from .templates.login import LOGIN_TEMPLATE
from ..controller import (Controller, get, post,
                          put, delete)
from ..auth.authentication_mw import login_required
from ..request import Request
from ..response import Response

class AdminController(Controller):
    """Admin dashboard controller."""

    @get("/login")
    async def login(self, req: Request) -> Response:
        """Login route for dashboard"""

        return await req.res.html_from_string(
            LOGIN_TEMPLATE
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
        return await req.res.html_from_string(
            "<h1>Model Table</h1><p>{{model_name}}</p>",
            {"model_name": model_name}
        )

    @get("/data/database/<string:db_name>/model/<string:model_name>/<int:record_id>")
    @login_required
    async def get_model_record(self, req: Request, db_name: str, 
                                    model_name: str, record_id: int) -> Response:
        """Get a specific model record."""
        return await req.res.html_from_string(
            "<h1>Model Record</h1><p>{{model_name}} - {{record_id}}</p>",
            {"model_name": model_name, "record_id": record_id}
        )

    @delete("/data/database/<string:db_name>/model/<string:model_name>/<int:record_id>")
    @login_required
    async def delete_model_record(self, req: Request, db_name: str, 
                                    model_name: str, record_id: int) -> Response:
        """Delete a specific model record."""
        return await req.res.html_from_string(
            "<h1>Deleted Record</h1><p>{{model_name}} - {{record_id}}</p>",
            {"model_name": model_name, "record_id": record_id}
        )

    @put("/data/database/<string:db_name>/model/<string:model_name>/<int:record_id>")
    @login_required
    async def patch_model_record(self, req: Request, db_name: str, 
                                    model_name: str, record_id: int) -> Response:
        """Patch a specific model record."""
        return await req.res.html_from_string(
            "<h1>Patched Record</h1><p>{{model_name}} - {{record_id}}</p>",
            {"model_name": model_name, "record_id": record_id}
        )

    @post("/data/database/<string:db_name>/model/<string:model_name>")
    @login_required
    async def create_model_record(self, req: Request, db_name: str, 
                                    model_name: str) -> Response:
        """Create a new model record."""
        return await req.res.html_from_string(
            "<h1>Created Record</h1><p>{{model_name}}</p>",
            {model_name: model_name}
        )
