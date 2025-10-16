"""
sql_database.py
Module for sql database connection/integration
"""

#import asyncio
from typing import Optional, Callable, cast, TYPE_CHECKING
from functools import wraps
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from pydantic import BaseModel, Field, ConfigDict

from ...utilities import run_sync_or_async
from ...base_extension import BaseExtension

if TYPE_CHECKING:
    from ...pyjolt import PyJolt

class SqlDatabaseConfig(BaseModel):
    """Configuration options for SqlDatabase extension"""
    model_config = ConfigDict(extra="allow")

    DATABASE_URI: str = Field(description="Connection string for the database")
    DATABASE_SESSION_NAME: str = Field("session", description="AsyncSession variable name for use with @managed_session decorator and @readonly_session decorator")

class SqlDatabase(BaseExtension):
    """
    A simple async Database interface using SQLAlchemy.
    """

    def __init__(self, db_name: str = "db", configs_name: str = "SQL_DATABASE") -> None:
        self._app: "Optional[PyJolt]" = None
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._db_uri: str = ""
        self._configs_name: str = configs_name
        self._configs: dict[str, str] = {}
        self.__db_name__ = db_name
        self._session_name: str = "session"

    def init_app(self, app: "PyJolt") -> None:
        """
        Initializes the database interface
        app.get_conf("DATABASE_URI") must return a connection string like:
        "postgresql+asyncpg://user:pass@localhost/dbname"
        or "sqlite+aiosqlite:///./pyjolt.db"
        """
        self._app = app
        self._configs = app.get_conf(self._configs_name, None)
        if self._configs is None:
            raise ValueError(f"Configurations for {self._configs_name} not found in app configurations.")
        self._configs = self.validate_configs(self._configs, SqlDatabaseConfig)
        self._db_uri = cast(str, self._configs.get("DATABASE_URI"))
        self._session_name = cast(str, self._configs.get("DATABASE_SESSION_NAME"))
        self._app.add_extension(self)
        self._app.add_on_startup_method(self.connect)
        self._app.add_on_shutdown_method(self.disconnect)

    async def connect(self) -> None:
        """
        Creates the async engine and session factory.
        Runs automatically when the lifespan.start signal is received
        """
        if not self._engine:
            self._engine = create_async_engine(
                cast(str, self._db_uri),
                echo=False,
                pool_pre_ping=True,
                pool_recycle=1800
            )

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            autoflush=False
        )
    
    async def disconnect(self) -> None:
        """
        Runs automatically when the lifespan.shutdown signal is received
        """
        if self._engine:
            await self._engine.dispose()
            self._engine = None

    def create_session(self) -> AsyncSession:
        """
        Creates new session and returns session object. Used for manual session handling.

        WARNING: You must close the session manually after use with await session.close()
        or use it within an async with block.
        """
        if self._session_factory is not None:
            return cast(AsyncSession, self._session_factory())
        #pylint: disable-next=W0719
        raise Exception("Session factory is None")

    async def execute_raw(self, statement, *, as_transaction: bool = False) -> list[RowMapping]:
        """
        Executes raw sql statement and returns list of RowMapping objects.
        
        If as_transaction is True, the execution will be wrapped in a transaction.
        as_transaction=False is for read-only state,emts; DML 
        """
        if not self._session_factory:
            raise RuntimeError("Database is not connected.")
        async with self._session_factory() as session:
            if as_transaction:
                async with session.begin():
                    result = await session.execute(statement)
            else:
                result = await session.execute(statement)
            return result.mappings().all()

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
        if self._engine is None:
            raise RuntimeError("Engine not initialized. Call connect() first.")
        return cast(AsyncEngine, self._engine)
    
    @property
    def session_name(self) -> str:
        """
        Returns the session variable name to be used in the kwargs of the request handler.
        Default is "session", can be changed via configuration.
        """
        return self._session_name

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
                    async with session.begin():  # Ensures transaction handling (auto commit/rollback)
                        kwargs[self.session_name] = session
                        return await run_sync_or_async(handler, *args, **kwargs)
            return wrapper
        return decorator
    
    @property
    def readonly_session(self) -> Callable:
        """
        Returns a decorator that:
        - Creates a new AsyncSession per request.
        - Injects it into the kwargs of the request with the key "session" or custom session name.
        - Closes the session automatically afterward.
        - Does not commit or rollback, for read-only operations.
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
                    kwargs[self.session_name] = session
                    return await run_sync_or_async(handler, *args, **kwargs)
            return wrapper
        return decorator
