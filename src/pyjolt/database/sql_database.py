"""
sql_database.py
Module for sql database connection/intergration
"""

#import asyncio
from typing import Optional, Callable, Any, cast, TYPE_CHECKING
from functools import wraps
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from pydantic import BaseModel, Field

from ..utilities import run_sync_or_async
from ..base_extension import BaseExtension

if TYPE_CHECKING:
    from ..pyjolt import PyJolt

class SqlDatabaseConfig(BaseModel):
    """Configuration options for SqlDatabase extension"""
    DATABASE_URI: str = Field(description="Connection string for the database")
    DATABASE_SESSION_NAME: str = Field("session", description="AsyncSession variable name for use with @managed_session decorator")

class SqlDatabase(BaseExtension):
    """
    A simple async Database interface using SQLAlchemy.
    """

    def __init__(self, db_name: str = "db", variable_prefix: str = "") -> None:
        self._app: "Optional[PyJolt]" = None
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._session: Optional[AsyncSession] = None
        self._db_uri: Optional[str] = None
        self._variable_prefix: str = variable_prefix
        self.__db_name__ = db_name
        self.session_name: str = "session"

    def init_app(self, app: "PyJolt") -> None:
        """
        Initilizes the database interface
        app.get_conf("DATABASE_URI") must return a connection string like:
        "postgresql+asyncpg://user:pass@localhost/dbname"
        or "sqlite+aiosqlite:///./test.db"
        """
        self._app = app
        self._db_uri = self._app.get_conf(f"{self._variable_prefix}DATABASE_URI")
        self.session_name = self._app.get_conf(f"{self._variable_prefix}DATABASE_SESSION_NAME",
                                               self.session_name)
        self._app.add_extension(self)
        self._app.add_on_startup_method(self.connect)
        self._app.add_on_shutdown_method(self.disconnect)

    async def connect(self) -> None:
        """
        Creates the async engine and session factory, if not already created.
        Also creates a single AsyncSession instance you can reuse.
        Runs automatically when the lifespan.start signal is received
        """
        if not self._engine:
            self._engine = create_async_engine(cast(str, self._db_uri), echo=False)

            self._session_factory = async_sessionmaker(
                bind=self._engine,
                expire_on_commit=True,
                autoflush=False
            )

    def create_session(self) -> AsyncSession:
        """
        Creates new session and returns session object
        """
        if self._session_factory is not None:
            return cast(AsyncSession, self._session_factory())
        #pylint: disable-next=W0719
        raise Exception("Session factory is None")

    async def commit(self) -> None:
        """
        Explicitly commits the current transaction.
        """
        if not self._session:
            raise RuntimeError("No session found. Did you forget to call `connect()`?")
        await self._session.commit()

    async def rollback(self) -> None:
        """
        Optional convenience for rolling back a transaction if something goes wrong.
        """
        if self._session:
            await self._session.rollback()

    async def disconnect(self) -> None:
        """
        Closes the active session and disposes of the engine.
        Runs automatically when the lifespan.shutdown signal is received
        """
        if self._session:
            await self._session.close()
            self._session = None

        if self._engine:
            await self._engine.dispose()
            self._engine = None

    async def execute_raw(self, statement) -> Any:
        """
        Optional: Execute a raw SQL statement. Useful if you have a custom query.
        """
        session = self.create_session()
        return await session.execute(statement)

    @property
    def db_uri(self):
        """
        Returns database connection uri string
        """
        return self._db_uri

    @property
    def engine(self) -> AsyncEngine:
        """
        Returns database engine
        """
        return cast(AsyncEngine, self._engine)

    @property
    def variable_prefix(self) -> str:
        """
        Return the config variables prefix string
        """
        return self._variable_prefix

    @property
    def db_name(self) -> str:
        return self.__db_name__

    @property
    def managed_session(self) -> Callable:
        """
        Returns a decorator that:
        - Creates a new AsyncSession per request.
        - Injects it into the kwargs of the request with the key "session" or custom session name.
        - Commits if no error occurs.
        - Rolls back if an unhandled error occurs.
        - Closes the session automatically afterward.
        """

        def decorator(handler: Callable) -> Callable:
            @wraps(handler)
            async def wrapper(*args, **kwargs):
                if not self._session_factory:
                    raise RuntimeError(
                        "Database is not connected. "
                        "Connection should be established automatically."
                        "Please check network connection and configurations."
                    )
                async with self._session_factory() as session:  # Ensures session closure
                    async with session.begin():  # Ensures transaction handling (auto commit/rolback)
                        kwargs[self.session_name] = session
                        return await run_sync_or_async(handler, *args, **kwargs)
            return wrapper
        return decorator
