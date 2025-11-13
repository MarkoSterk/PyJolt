# base_protocol.py
#pylint: disable=W0613

from __future__ import annotations
from typing import Optional

from sqlalchemy.inspection import inspect
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession
from .sqlalchemy_async_query import AsyncQuery

class DeclarativeBaseModel(DeclarativeBase):
    """
    Defines the interface that the custom
    DeclarativeBase class must satisfy.
    """
    __db_name__: str
    __abstract__ = True

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

    @classmethod
    def query(cls, session: AsyncSession) -> AsyncQuery:
        return AsyncQuery(session, cls)

    @classmethod
    def db_name(cls) -> str:
        return cls.__db_name__
    
    @classmethod
    def primary_key_name(cls) -> Optional[str]:
        """
        Returns the attribute name of the primary key column.
        If a composite primary key exists, returns the first one.
        """
        mapper = inspect(cls)
        pks = mapper.primary_key

        if not pks:
            return None

        return pks[0].key


