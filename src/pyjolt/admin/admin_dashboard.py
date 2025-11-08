"""Admin dashboard extension"""
from typing import TYPE_CHECKING, Type, Any
from pydantic import BaseModel, Field
from ..base_extension import BaseExtension
from .admin_controller import AdminController
from ..database.sql.base_protocol import DeclarativeBaseModel
from ..controller import path

if TYPE_CHECKING:
    from ..pyjolt import PyJolt

class AdminDashboardConfig(BaseModel):
    """Admin dashboard configuration model."""

    DASHBOARD_URL: str = Field(
        default="/admin/dashboard",
        description="URL path for accessing the admin dashboard."
    )


class AdminDashboard(BaseExtension):
    """Admin dashboard extension class."""

    def __init__(self) -> None:
        self._databases_models: dict[str, list[Type[DeclarativeBaseModel]]] = {}
        self._configs: dict[str, Any] = {}

    def init_app(self, app: "PyJolt") -> None:
        self._app = app
        self._configs = app.get_conf(self._configs_name, {})
        self._configs = self.validate_configs(self._configs, AdminDashboardConfig)
        #pylint: disable-next=W0212
        self._databases_models = self._app._db_models
        controller: Type[AdminController] = path(url_path=self._configs["DASHBOARD_URL"],
                                                 open_api_spec=False)(AdminController)
        self._app.register_controller(controller)

    def get_model(self, db_name: str, model_name: str) -> Type[DeclarativeBaseModel] | None:
        """Get a model class by database name and model name."""
        models = self._databases_models.get(db_name, [])
        for model in models:
            if model.__name__ == model_name:
                return model
        return None
