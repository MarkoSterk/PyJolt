# base_protocol.py
#pylint: disable=W0613

from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from .sqlalchemy_models import AsyncQuery

class BaseModel:
    """
    Defines the interface that the custom
    DeclarativeBase class must satisfy.
    """

    metadata: MetaData

    @classmethod
    def query(cls, session: AsyncSession) -> "AsyncQuery": # type: ignore[empty-body]
        pass

    @classmethod
    def db_name(cls) -> str: # type: ignore[empty-body]
        pass
