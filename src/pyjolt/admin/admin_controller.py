"""Admin controller module."""
import os
import mimetypes
from typing import Any, Optional, Type, TYPE_CHECKING, cast
from sqlalchemy.inspection import inspect
from werkzeug.utils import safe_join
from pydantic import BaseModel, Field
from datetime import datetime
from .utilities import PermissionType, FormType, extract_table_columns
from ..database.sql.declarative_base import DeclarativeBaseModel
from .templates.login import LOGIN_TEMPLATE
from .templates.model_table import MODEL_TABLE, MODEL_TABLE_STYLE, MODEL_TABLE_SCRIPTS
from .templates.dashboard import DASHBOARD, DASHBOARD_STYLE
from .templates.database import DATABASE
from .templates.denied_entry import DENIED_ENTRY
from .templates.base import get_template_string
from ..controller import (Controller, get, post,
                          put, delete)
from ..request import Request
from ..response import Response
from ..http_statuses import HttpStatus
from ..exceptions.http_exceptions import BaseHttpException, StaticAssetNotFound
from ..auth.authentication_mw import login_required
from ..database.sql import SqlDatabase, AsyncSession, AsyncQuery
from ..utilities import get_file, get_range_file
from .form_fields import DateTimePickerField

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

class AdminEnterError(BaseHttpException):
    """Error for when a user does not have permission to enter the dashboard"""
    def __init__(self, user):
        super().__init__("User doesn't have access to admin dashboard",
                         HttpStatus.UNAUTHORIZED, "error", user)

class PaginationModel(BaseModel):
    """Simple pagination model"""
    page: int = Field(1, description="Requested page")
    per_page: int = Field(12, description="Requested number of results per page")

class AdminController(Controller):
    """Admin dashboard controller."""

    _dashboard: "AdminDashboard"

    @get("/login")
    async def login(self, req: Request) -> Response:
        """Login route for dashboard"""
        return await req.res.html_from_string(
            LOGIN_TEMPLATE,
            {"configs": self.dashboard.configs}
        )

    @get("/")
    @login_required
    async def index(self, req: Request) -> Response:
        """Get admin dashboard data."""
        if not (await self.can_enter(req)):
            return await self.cant_enter_response(req)
        overviews: dict[str, Any] = await self.dashboard.databases_overviews()
        return await req.res.html_from_string(get_template_string(DASHBOARD), {
            "configs": self.dashboard.configs, "styles": [DASHBOARD_STYLE],
            "num_of_db": overviews["db_count"], "schemas_count": overviews["schemas_count"],
            "tables_count": overviews["tables_count"],"views_count": overviews["views_count"],
            "rows_count": overviews["rows_count"], "columns_count": overviews["columns_count"],
            "all_dbs": self.dashboard.all_dbs, "database_models": self.dashboard._databases_models
        })
    
    @get("/database/<string:db_name>")
    @login_required
    async def database(self, req: Request, db_name: str) -> Response:
        """Get admin dashboard data."""
        if not (await self.can_enter(req)):
            return await self.cant_enter_response(req)
        overview: dict[str, Any] = await self.dashboard.database_overview(db_name, with_extras=True)
        db: SqlDatabase = self.dashboard.get_database(db_name)
        return await req.res.html_from_string(get_template_string(DATABASE), {
            "configs": self.dashboard.configs, "styles": [DASHBOARD_STYLE],
            "schemas_count": overview["schemas_count"],
            "tables_count": overview["tables_count"],"views_count": overview["views_count"],
            "rows_count": overview["rows_count"], "columns_count": overview["columns_count"],
            "size_bytes": overview.get("extras", {}).get("db_size_bytes", None),
            "db": self.dashboard.get_database(db_name), "all_dbs": self.dashboard.all_dbs,
            "models_list": db.models_list, "db_name": db_name, "database_models": self.dashboard._databases_models
        })

    @get("/data/database/<string:db_name>/model/<string:model_name>")
    @login_required
    async def model_table(self, req: Request, db_name: str,
                                    model_name: str) -> Response:
        """Model table with records."""
        if not (await self.can_enter(req)):
            return await self.cant_enter_response(req)
        model = await self.check_permission(PermissionType.CAN_VIEW, req, db_name, model_name)
        pagination = PaginationModel.model_validate(req.query_params)
        database: SqlDatabase = self.dashboard.get_database(db_name)
        session: AsyncSession = self.dashboard.get_session(database)
        query: AsyncQuery = model.query(session)
        ordering: Optional[list[str]] = model.order_table_by()
        if ordering is not None:
            query = query.order_by_strings(
                *ordering
            )
        all_data: dict[str, Any] = {}
        if pagination.per_page > 0:
            all_data= await query.paginate(page=pagination.page, per_page=pagination.per_page)
        else:
            all_data["items"] = await query.all()
            all_data["pages"] = 0
        await session.close()
        columns = extract_table_columns(model, exclude=getattr(model.Meta, "exclude_from_table", None))
        relationships_tuples = inspect(model).relationships.items()#type: ignore[union-attr]
        relationships: list[str] = []
        if relationships_tuples is not None:
            relationships=[rel[0] for rel in relationships_tuples]
        generated_form = self.dashboard.get_model_form(model,
                                                   form_type=FormType.EDIT,
                                                   exclude_pk = True,
                                                   exclude=relationships
                                                   )
        model_form: list[Any] = cast(list[Any], [field for field in generated_form()])
        additional_fields = model.add_to_form()
        for field_id, field in additional_fields.items():
            setattr(field, "id", field_id)
            model_form.append(field)
        create_permission: bool = await self.dashboard.has_create_permission(req, model)
        delete_permission: bool = await self.dashboard.has_delete_permission(req, model)
        update_permission: bool = await self.dashboard.has_update_permission(req, model)
        return await req.res.html_from_string(
            get_template_string(MODEL_TABLE),
            {"model_name": model_name, "all_data": all_data, "pk_names": model.primary_key_names(),
             "columns": columns, "title": f"{model_name} Table", "create_path": self.create_attr_val_path_for_model,
             "db_nice_name": database.nice_name, "db_name": db_name, "db": database,
             "styles": [MODEL_TABLE_STYLE], "configs": self.dashboard.configs, "model": model,
             "scripts": [MODEL_TABLE_SCRIPTS], "all_dbs": self.dashboard.all_dbs,
             "model_form": model_form, "database_models": self.dashboard._databases_models,
             "datetime_field": DateTimePickerField(classes=["form-control", "dashboard-input"]),
             "can_create": create_permission, "can_delete": delete_permission, "can_update": update_permission}
        )

    @get("/data/database/<string:db_name>/model/<string:model_name>/<path:attr_val>")
    @login_required
    async def get_model_record(self, req: Request, db_name: str,
                                    model_name: str, attr_val: str) -> Response:
        """Get a specific model record."""
        if not (await self.can_enter(req)):
            return await self.cant_enter_response(req)
        model = await self.check_permission(PermissionType.CAN_VIEW, req, db_name, model_name)
        db: SqlDatabase = self.dashboard.get_database(db_name)
        model_pk_val: dict[str, str] = self.parse_key_value_path(attr_val)
        filters = self.get_pk_filters_from_path(model, model_pk_val)
        async with db.create_session() as session:
            async with session.begin():
                record = await model.query(session).filter(*filters).first()
                if record is None:
                    raise UnknownModelError(db_name, model_name)
        data = {}
        for column in model.__table__.columns:
            value = getattr(record, column.key)
            if isinstance(value, datetime):
                value = value.isoformat()
            data[column.key] = value
        return req.res.json({
            "message": "Record data fetched successfully.",
            "status": "success",
            "data": data
        }).status(HttpStatus.OK)

    #API calls for the admin dashboard
    #DELETE, PUT, CREATE operations
    @delete("/data/database/<string:db_name>/model/<string:model_name>/<path:attr_val>")
    @login_required
    async def delete_model_record(self, req: Request, db_name: str,
                                    model_name: str, attr_val: str) -> Response:
        """Delete a specific model record."""
        if not (await self.can_enter(req)):
            return await self.cant_enter_response(req)
        model = await self.check_permission(PermissionType.CAN_DELETE, req, db_name, model_name)
        db: SqlDatabase = self.dashboard.get_database(db_name)
        model_pk_val: dict[str, str] = self.parse_key_value_path(attr_val)
        filters = self.get_pk_filters_from_path(model, model_pk_val)
        async with db.create_session() as session:
            async with session.begin():
                record = await model.query(session).filter(*filters).first()
                if record is not None:
                    await session.delete(record)
                else:
                    return req.res.json({
                        "message": f"Record in {model_name} not found.",
                        "status": "error"
                    }).status(HttpStatus.NOT_FOUND)
        self.app.logger.info(f"Admin dashboard - deleted {model_name=} with {attr_val}")
        return req.res.no_content()

    @put("/data/database/<string:db_name>/model/<string:model_name>/<path:attr_val>")
    @login_required
    async def put_model_record(self, req: Request, db_name: str,
                                    model_name: str, attr_val: str) -> Response:
        """Patch a specific model record."""
        if not (await self.can_enter(req)):
            return await self.cant_enter_response(req)
        model: Type[DeclarativeBaseModel] = await self.check_permission(PermissionType.CAN_EDIT, req, db_name, model_name)
        data: dict[str, Any] = cast(dict[str, Any], await req.json())
        validation_schema = model.update_validation_schema()
        if validation_schema is not None:
            data = validation_schema.model_validate(data).model_dump()
        db: SqlDatabase = self.dashboard.get_database(db_name)
        model_pk_val: dict[str, str] = self.parse_key_value_path(attr_val)
        filters = self.get_pk_filters_from_path(model, model_pk_val)
        async with db.create_session() as session:
            async with session.begin():
                record: DeclarativeBaseModel = await model.query(session).filter(*filters).first()
                if record is not None:
                    await record.admin_update(req, data, session)
                    session.add(record)
                else:
                    return req.res.json({
                        "message": f"Record in {model_name} not found.",
                        "status": "error"
                    }).status(HttpStatus.NOT_FOUND)
        return req.res.json({
            "message": f"Record in {model_name} updated successfully.",
            "status": "success"
        }).status(HttpStatus.OK)

    @post("/data/database/<string:db_name>/model/<string:model_name>")
    @login_required
    async def create_model_record(self, req: Request, db_name: str, 
                                    model_name: str) -> Response:
        """Create a new model record."""
        if not (await self.can_enter(req)):
            return await self.cant_enter_response(req)
        model = await self.check_permission(PermissionType.CAN_CREATE, req, db_name, model_name)
        data: dict[str, Any] = cast(dict[str, Any], await req.json())
        validation_schema = model.create_validation_schema()
        if validation_schema is not None:
            data = validation_schema.model_validate(data).model_dump()
        db: SqlDatabase = self.dashboard.get_database(db_name)
        async with db.create_session() as session:
            async with session.begin():
                record = model()
                await record.admin_create(req, data, session)
                session.add(record)

        return req.res.json({
            "message": f"Record in {model_name} created successfully.",
            "status": "success"
        }).status(HttpStatus.CREATED)
    
    async def cant_enter_response(self, req: Request) -> Response:
        """Response for when a user cannot enter the dashboard"""
        return (await req.res.html_from_string(
            DENIED_ENTRY
        )).status(HttpStatus.UNAUTHORIZED)

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

    async def can_enter(self, req: Request) -> bool:
        """
        Method for checking permission to enter
        admin dashboard
        """
        has_permission: bool = False
        has_permission = await self.dashboard.has_enter_permission(req)
        return has_permission

    async def check_permission(self, perm_type: PermissionType,
                               req: Request,
                               db_name: str,
                               model_name: str) -> Type[DeclarativeBaseModel]:
        """Method for checking permissions for admin actions"""

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
            has_permission = await self.dashboard.has_update_permission(req, model)
        else:
            has_permission = await self.dashboard.has_delete_permission(req, model)

        if not has_permission:
            raise AdminPermissionError("User does not have permission "
                                          f"to {perm_type} model data in {db_name} database.")
        return model
    
    def parse_key_value_path(self, s: str) -> dict[str, str]:
        """
        Parse a string like "id1/val1/id2/val2" into {"id1": "val1", "id2": "val2"}.
        Requires an even number of segments.
        """
        parts = s.split("/")
        if len(parts) % 2 != 0:
            raise ValueError(f"Invalid key/value path: {s!r}")

        return {parts[i]: parts[i + 1] for i in range(0, len(parts), 2)}
    
    def get_pk_filters_from_path(self, model: Type[DeclarativeBaseModel],
                                 model_pk_val: dict[str, str]) -> list:
        """Returns a list of filters"""
        filters: list = []
        for pk, val in model_pk_val.items():
            pk_attr = model.__table__.columns[pk]
            pk_val = pk_attr.type.python_type(val)
            filters.append(pk_attr == pk_val)
        return filters
    
    @staticmethod
    def create_attr_val_path_for_model(model, pk_names) -> str:
        """Creates url path for model with PKs and values"""
        path: str = ""
        for pk in pk_names:
            path+=f"/{pk}/{getattr(model, pk)}"
        return path[1:]

    @property
    def dashboard(self) -> "AdminDashboard":
        return self._dashboard
