"""
Interface for connecting to a MongoDB database
"""
from typing import Optional, Callable, Any
from functools import wraps
from pymongo import IndexModel

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .base_nosql_database import BaseNoSqlDatabase
from ...pyjolt import PyJolt

class MongoDatabase(BaseNoSqlDatabase):
    """MongoDB interface"""

    def __init__(self, app: PyJolt = None, variable_prefix: str = ""):
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        self._db_uri: str = None
        self._db_name: str = None
        self._variable_prefix = variable_prefix
        if app:
            self.init_app(app)

    def init_app(self, app: PyJolt) -> None:
        """
        Initializes the database interface.
        Expects `DATABASE_URI` and `DATABASE_NAME` in app config.
        Example: 
            "mongodb://user:pass@localhost:27017/dbname"
        """
        self._db_uri = app.get_conf(f"{self._variable_prefix}DATABASE_URI")
        self._db_name = app.get_conf(f"{self._variable_prefix}DATABASE_NAME")

        if not self._db_uri or not self._db_name:
            raise ValueError("DATABASE_URI and DATABASE_NAME must be configured")

        app.add_extension(self)
        app.add_on_startup_method(self.connect)
        app.add_on_shutdown_method(self.disconnect)
        app.add_dependency_injection_to_map(AsyncIOMotorDatabase, self.get_database)

    async def connect(self, _) -> None:
        """
        Connects to MongoDB on startup.
        """
        if not self._client:
            self._client = AsyncIOMotorClient(self._db_uri)
            self._database = self._client[self._db_name]

    async def disconnect(self, _) -> None:
        """
        Closes MongoDB connection on shutdown.
        """
        if self._client:
            self._client.close()
            self._client = None
            self._database = None

    def get_database(self) -> AsyncIOMotorDatabase:
        """
        Returns the active database instance.
        """
        if not self._database:
            raise RuntimeError("Database not connected. Call `await connect()` first.")
        return self._database

    async def create_collection(self, name: str,
                                indexes: list[IndexModel] = None) -> None:
        """
        Creates a collection with optional indexes.
        """
        if name not in await self._database.list_collection_names():
            collection = self._database[name]
            if indexes:
                await collection.create_indexes(indexes)

    async def drop_collection(self, name: str) -> None:
        """
        Drops a collection.
        """
        if name in await self._database.list_collection_names():
            await self._database.drop_collection(name)

    async def execute_raw(self, command: dict) -> Any:
        """
        Executes a raw MongoDB command.
        """
        return await self._database.command(command)

    @property
    def db_uri(self):
        """
        Returns the MongoDB connection URI.
        """
        return self._db_uri

    @property
    def database(self) -> AsyncIOMotorDatabase:
        """
        Returns the database instance.
        """
        return self._database

    @property
    def with_session(self) -> Callable:
        """
        Returns a decorator that injects a MongoDB session into the route handler.
        Handles transactions (if using a replica set).
        """
        def decorator(handler) -> Callable:
            @wraps(handler)
            async def wrapper(*args, **kwargs):
                if not self._client:
                    raise RuntimeError(
                        "Database is not connected. "
                        "Connection should be established automatically."
                    )
                async with await self._client.start_session() as session:
                    kwargs["session"] = session
                    return await handler(*args, **kwargs)
            return wrapper
        return decorator
