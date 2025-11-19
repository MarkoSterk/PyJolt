# base_protocol.py
#pylint: disable=W0613

from __future__ import annotations
from typing import Any, Optional, Tuple, cast, Type
from pydantic import BaseModel

from sqlalchemy import Column
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession
from .sqlalchemy_async_query import AsyncQuery

from ...request import Request

class DeclarativeBaseModel(DeclarativeBase):
    """
    Defines the interface that the custom
    DeclarativeBase class must satisfy.
    """
    __db_name__: str
    __abstract__ = True

    class AdminDashboardMeta:
        pass

    def __init__(self, **kwargs):
        if kwargs is not None:
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.__abstract__:
            if "__db_name__" not in cls.__dict__:
                raise TypeError(
                    f"{cls.__name__} must define a class attribute '__db_name__'"
                )

    async def admin_save(self, req: "Request", new_data: dict[str, Any], session: "AsyncSession") -> None:
        """
        Saves the current instance to the database. Used in admin dashboard forms
        for creating and editing records. If customization is needed, override this method
        in the model class.
        """
        for key, value in new_data.items():
            setattr(self, key, value)
    
    async def admin_delete(self, req: "Request", session: "AsyncSession") -> None:
        """
        Deletes the current instance from the database. Used in admin dashboard
        for deleting records. If customization is needed, override this method
        in the model class.
        """
        pass
    
    async def admin_update(self, req: "Request", new_data: dict[str, Any], session: "AsyncSession") -> None:
        """
        Updates the current instance with new data. Used in admin dashboard
        forms for editing records. If customization is needed, override this method
        in the model class.
        """
        for key, value in new_data.items():
            setattr(self, key, value)

    @classmethod
    def query(cls, session: AsyncSession) -> AsyncQuery:
        return AsyncQuery(session, cls)

    @classmethod
    def db_name(cls) -> str:
        return cls.__db_name__
    
    @classmethod
    def primary_key_names(cls) -> Optional[list[str]]:
        """
        Returns the attribute names of the primary key columns.
        """
        mapper = inspect(cls)
        pks = mapper.primary_key

        if not pks:
            return None

        return [pk.key for pk in pks]#pks[0].key
    
    @classmethod
    def primary_keys(cls) -> Optional[Tuple[Column[Any]]]:
        mapper = inspect(cls)
        pks = mapper.primary_key
        if not pks:
            return None
        return cast(Tuple[Column[Any]], pks)
    
    @classmethod
    def exclude_in_form(cls) -> list[str]:
        """Returns all fields that are declared as hidden in the form"""
        if not hasattr(cls.AdminDashboardMeta, "exclude_in_form"):
            return []
        return cls.AdminDashboardMeta.exclude_in_form
    
    @classmethod
    def exclude_in_table(cls) -> list[str]:
        """Returns all fields that are declared as excluded in the table"""
        if not hasattr(cls.AdminDashboardMeta, "exclude_in_table"):
            return []
        return cls.AdminDashboardMeta.exclude_in_table
    
    @classmethod
    def form_labels_map(cls) -> dict[str, str]:
        """Map of attribute names -> human readable names"""
        if not hasattr(cls.AdminDashboardMeta, "custom_labels"):
            return {}
        return cls.AdminDashboardMeta.custom_labels
    
    @classmethod
    def custom_form_fields(cls) -> dict[str, Any]:
        """Returns custom form fields for the admin dashboard forms"""
        if not hasattr(cls.AdminDashboardMeta, "custom_form_fields"):
            return {}
        return cls.AdminDashboardMeta.custom_form_fields
    
    @classmethod
    def create_validation_schema(self) -> Optional[Type[BaseModel]]:
        """Returns the schema used for validating creation forms in admin dashboard"""
        if not hasattr(self.AdminDashboardMeta, "create_validation_shema"):
            return None
        return self.AdminDashboardMeta.create_validation_shema
    
    @classmethod
    def edit_validation_schema(self) -> Optional[Type[BaseModel]]:
        """Returns the schema used for validating edit forms in admin dashboard"""
        if not hasattr(self.AdminDashboardMeta, "edit_validation_shema"):
            return None
        return self.AdminDashboardMeta.edit_validation_shema


