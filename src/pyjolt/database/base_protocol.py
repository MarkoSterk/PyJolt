# base_protocol.py
from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Protocol, runtime_checkable, Optional

from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from .sqlalchemy_models import AsyncQuery

@runtime_checkable
class BaseModelProtocol(Protocol):
    """
    This protocol defines the interface that the custom
    DeclarativeBase class must satisfy.
    """

    @classmethod
    def query(cls, session: Optional[AsyncSession] = None) -> "AsyncQuery":
        pass
