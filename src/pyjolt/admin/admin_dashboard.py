"""Admin dashboard extension"""
import os
from abc import abstractmethod
from typing import TYPE_CHECKING, Optional, Type, Any
from pydantic import BaseModel, Field
from wtforms_sqlalchemy.orm import model_form
from ..exceptions.runtime_exceptions import CustomException
from .utilities import FormType
from ..base_extension import BaseExtension
from .admin_controller import AdminController
from ..database.sql.base_protocol import DeclarativeBaseModel
from ..controller import path
from ..request import Request
from ..database.sql import SqlDatabase, AsyncSession

if TYPE_CHECKING:
    from ..pyjolt import PyJolt

class AdminDashboardConfig(BaseModel):
    """Admin dashboard configuration model."""

    DASHBOARD_URL: Optional[str] = Field(
        "/admin/dashboard",
        description="URL path for accessing the admin dashboard."
    )

    URL_FOR_FOR_LOGIN: str = Field(description="The url_for string for your login endpoint")
    URL_FOR_FOR_LOGOUT: str = Field(description="The url_for string for your logout endpoint")

class AdminMissingDatabaseExtension(CustomException):
    def __init__(self, db_name: str):
        self.message = ("Failed to load database extension with "
                        f"{db_name=}")

class AdminDashboard(BaseExtension):
    """Admin dashboard extension class."""

    def __init__(self) -> None:
        self._databases_models: dict[str, list[Type[DeclarativeBaseModel]]] = {}
        self._configs: dict[str, Any] = {}
        self._configs_name: str = "ADMIN_DASHBOARD"
        self._root_path = os.path.dirname(__file__)

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
    
    def get_model_form(self, model: Type[DeclarativeBaseModel],
                       form_type: str = FormType.EDIT, 
                       exclude_pk: bool = False, exclude_fk: bool = True,
                       only: Any | None = None, exclude: Any | None = None,
                       field_args: Any | None = None, converter: Any | None = None,
                       type_name: Any | None = None) -> Type:
        """
            Get a WTForms-SQLAlchemy form for a given model.

            Args:
                only (Iterable[str], optional):  
                    Property names that should be included in the form.  
                    Only these properties will have fields.

                exclude (Iterable[str], optional):  
                    Property names that should be excluded from the form.  
                    All other properties will have fields.

                field_args (dict[str, dict], optional):  
                    A mapping of field names to keyword arguments used to construct
                    each field object.

                converter (Type[ModelConverter], optional):  
                    A converter class used to generate fields based on the model
                    properties. If not provided, ``ModelConverter`` is used.

                exclude_pk (bool, optional):  
                    Whether to force exclusion of primary key fields. Defaults to ``False``.

                exclude_fk (bool, optional):  
                    Whether to force exclusion of foreign key fields. Defaults to ``False``.

                type_name (str, optional):  
                    Custom name for the generated form class.

            Returns:
                Type[Form]: A dynamically generated WTForms form class.
        """
        if hasattr(model, f"__{form_type}_form__"):
            return getattr(model, f"__{form_type}_form__")
        form_class = model_form(model, exclude_pk=exclude_pk, only=only, exclude=exclude,
                                field_args=field_args, converter=converter,
                                exclude_fk=exclude_fk, type_name=type_name)
        setattr(model, f"__{form_type}_form__", form_class)
        return form_class

    def get_database(self, db_name: str) -> "SqlDatabase":
        for _, ext in self.app.extensions.items():
            if isinstance(ext, SqlDatabase):
                if ext.db_name == db_name:
                    return ext
        raise AdminMissingDatabaseExtension(db_name)
    
    def get_session(self, database: "SqlDatabase") -> "AsyncSession":
        return database.create_session()

    @property
    def configs(self) -> dict[str, Any]:
        """Dictonary with dashboard configs"""
        return self._configs

    @property
    def root_path(self) -> str:
        return self._root_path

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
