# base_protocol.py
from __future__ import annotations

import typing
from typing import Protocol, Callable, Optional

from sqlalchemy.ext.asyncio import AsyncSession

# Forward-declare AsyncQuery so we can refer to it in Protocol.
# You can also import it directly if that fits your code structure better.
if typing.TYPE_CHECKING:
    from . import AsyncQuery

class BaseModelProtocol(Protocol):
    """
    This protocol defines the interface that the custom
    DeclarativeBase class must satisfy.
    """
    __abstract__ = True
    _session_factory: Optional[Callable[..., AsyncSession]]

    @classmethod
    def add_session_factory(cls, factory: Callable[..., AsyncSession]) -> None:
        pass

    @classmethod
    def query(cls, session: Optional[AsyncSession] = None) -> AsyncQuery:
        pass
