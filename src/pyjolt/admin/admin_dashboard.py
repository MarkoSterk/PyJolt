"""Admin dashboard extension"""
from abc import abstractmethod
from typing import TYPE_CHECKING, Optional, Type, Any
from pydantic import BaseModel, Field
from ..base_extension import BaseExtension
from .admin_controller import AdminController
from ..database.sql.base_protocol import DeclarativeBaseModel
from ..controller import path
from ..request import Request

if TYPE_CHECKING:
    from ..pyjolt import PyJolt

class AdminDashboardConfig(BaseModel):
    """Admin dashboard configuration model."""

    DASHBOARD_URL: Optional[str] = Field(
        "/admin/dashboard",
        description="URL path for accessing the admin dashboard."
    )

    URL_FOR_FOR_LOGIN: str = Field(description="The url_for string for your login endpoint")


class AdminDashboard(BaseExtension):
    """Admin dashboard extension class."""

    def __init__(self) -> None:
        self._databases_models: dict[str, list[Type[DeclarativeBaseModel]]] = {}
        self._configs: dict[str, Any] = {}
        self._configs_name: str = "ADMIN_DASHBOARD"

    def init_app(self, app: "PyJolt") -> None:
        self._app = app
        self._configs = app.get_conf(self._configs_name, {})
        self._configs = self.validate_configs(self._configs, AdminDashboardConfig)
        #pylint: disable-next=W0212
        self._databases_models = self._app._db_models
        controller: Type[AdminController] = path(url_path=self._configs["DASHBOARD_URL"],
                                                 open_api_spec=False)(AdminController)
        setattr(controller, "_dashboard", self)
        self._app.register_controller(controller)

    def get_model(self, db_name: str, model_name: str) -> Type[DeclarativeBaseModel] | None:
        """Get a model class by database name and model name."""
        models = self._databases_models.get(db_name, [])
        for model in models:
            if model.__name__ == model_name:
                return model
        return None

    @abstractmethod
    async def has_enter_permission(self, req: Request) -> bool:
        """If a user can enter the dashboard"""

    @abstractmethod
    async def has_view_permission(self, req: Request, model: Type[DeclarativeBaseModel]) -> bool:
        """If the logged in user has permission to view model data"""

    @abstractmethod
    async def has_edit_permission(self, req: Request, model: Type[DeclarativeBaseModel]) -> bool:
        """If the logged in user has permission to edit model data"""

    @abstractmethod
    async def has_create_permission(self, req: Request, model: Type[DeclarativeBaseModel]) -> bool:
        """If the logged in user has permission to create model data"""

    @abstractmethod
    async def has_delete_permission(self, req: Request, model: Type[DeclarativeBaseModel]) -> bool:
        """If the logged in user has permission to delete model data"""
