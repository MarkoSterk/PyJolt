"""Admin controller module."""
from ..controller import (Controller, get, post,
                          put, delete)
from ..request import Request
from ..response import Response

class AdminController(Controller):
    """Admin dashboard controller."""

    @get("/")
    async def index(self, req: Request) -> Response:
        """Get admin dashboard data."""
        return await req.res.html_from_string("<h1>Admin Dashboard</h1>")
    
    @get("/data/database/<string:db_name>/model/<string:model_name>")
    async def model_table(self, req: Request, db_name: str, 
                                    model_name: str) -> Response:
        """Handle model table operations."""
        return await req.res.html_from_string(
            "<h1>Model Table</h1><p>{{model_name}}</p>",
            {"model_name": model_name}
        )
    
    @get("/data/database/<string:db_name>/model/<string:model_name>/<int:record_id>")
    async def get_model_record(self, req: Request, db_name: str, 
                                    model_name: str, record_id: int) -> Response:
        """Get a specific model record."""
        return await req.res.html_from_string(
            "<h1>Model Record</h1><p>{{model_name}} - {{record_id}}</p>",
            {"model_name": model_name, "record_id": record_id}
        )
    
    @delete("/data/database/<string:db_name>/model/<string:model_name>/<int:record_id>")
    async def delete_model_record(self, req: Request, db_name: str, 
                                    model_name: str, record_id: int) -> Response:
        """Delete a specific model record."""
        return await req.res.html_from_string(
            "<h1>Deleted Record</h1><p>{{model_name}} - {{record_id}}</p>",
            {"model_name": model_name, "record_id": record_id}
        )
    
    @put("/data/database/<string:db_name>/model/<string:model_name>/<int:record_id>")
    async def patch_model_record(self, req: Request, db_name: str, 
                                    model_name: str, record_id: int) -> Response:
        """Patch a specific model record."""
        return await req.res.html_from_string(
            "<h1>Patched Record</h1><p>{{model_name}} - {{record_id}}</p>",
            {"model_name": model_name, "record_id": record_id}
        )
    
    @post("/data/database/<string:db_name>/model/<string:model_name>")
    async def create_model_record(self, req: Request, db_name: str, 
                                    model_name: str) -> Response:
        """Create a new model record."""
        return await req.res.html_from_string(
            "<h1>Created Record</h1><p>{{model_name}}</p>",
            {model_name: model_name}
        )
    
