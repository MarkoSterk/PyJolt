"""
Base/abstract class for implementing 
classes for different NoSqlDatabases
"""
from abc import ABC, abstractmethod
from typing import Any

from ...pyjolt import PyJolt

class BaseNoSqlDatabase(ABC):
    """
    Abstract Base Class for NoSQL databases.
    """

    @abstractmethod
    async def connect(self, app: PyJolt) -> None:
        pass

    @abstractmethod
    async def disconnect(self, app: PyJolt) -> None:
        pass

    @abstractmethod
    async def create_collection(self, name: str) -> None:
        pass

    @abstractmethod
    async def drop_collection(self, name: str) -> None:
        pass

    @abstractmethod
    async def execute_raw(self, command: Any) -> Any:
        pass
