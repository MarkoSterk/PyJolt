"""
sql_database.py
Module for sql database connection/intergration
"""

#import asyncio
from typing import Optional, Callable, Any, Type
from functools import wraps
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    AsyncSession,
)
from sqlalchemy.orm import sessionmaker

from .sqlalchemy_models import create_declerative_base
from ..utilities import run_sync_or_async
from ..pyjolt import PyJolt
from .base_protocol import BaseModelProtocol


class SqlDatabase:
    """
    A simple async Database interface using SQLAlchemy.
    It handles:
    engine creation
    session creation
    explicit commit
    connect & disconnect (dispose)
    """

    def __init__(self, app: PyJolt = None, variable_prefix: str = ""):
        self._app: PyJolt = None
        self._engine: Optional[AsyncEngine] = None
        self._session_factory = None
        self._session: Optional[AsyncSession] = None
        self._db_uri: str = None
        self._variable_prefix: str = variable_prefix
        self._declerative_base = None
        if app:
            self.init_app(app)

    def init_app(self, app: PyJolt) -> None:
        """
        Initilizes the database interface
        app.get_conf("DATABASE_URI") must returns a connection string like:
        "postgresql+asyncpg://user:pass@localhost/dbname"
        or "sqlite+aiosqlite:///./test.db"
        """
        self._app = app
        self._db_uri = self._app.get_conf(f"{self._variable_prefix}DATABASE_URI")
        db_name: str = self._app.get_conf(f"{self._variable_prefix}DATABASE_NAME", False)
        if db_name is not False:
            self.__name__ = db_name
        
        self._declerative_base = create_declerative_base()
        self._declerative_base.add_session_factory(self.create_session)
        self._app.add_extension(self)
        self._app.add_on_startup_method(self.connect)
        self._app.add_on_shutdown_method(self.disconnect)
        self._app.add_dependency_injection_to_map(AsyncSession, self.create_session)

    async def connect(self, _) -> None:
        """
        Creates the async engine and session factory, if not already created.
        Also creates a single AsyncSession instance you can reuse.
        Runs automatically when the lifespan.start signal is received
        """
        if not self._engine:
            self._engine = create_async_engine(self._db_uri, echo=False)

            self._session_factory = sessionmaker(
                bind=self._engine,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
                class_=AsyncSession,
            )

        # if not self._session:
        #     # Create a session instance to be used throughout the app
        #     self._session = self._session_factory()
    
    def create_session(self) -> AsyncSession:
        """
        Creates new session and returns session object
        """
        return self._session_factory()

    def get_session(self) -> AsyncSession:
        """
        Returns the current session. You typically call this inside your request handlers
        or services to do queries, inserts, etc.
        """
        if not self._session:
            raise RuntimeError("Database not connected. Call `await connect()` first.")
        return self._session

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

    async def disconnect(self, _) -> None:
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
        session = self.get_session()
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
        return self._engine

    @property
    def variable_prefix(self) -> str:
        """
        Return the config variables prefix string
        """
        return self._variable_prefix
    
    @property
    def Model(self) -> Type[BaseModelProtocol]:
        """
        Returns base model for all model classes
        """
        return self._declerative_base

    @property
    def with_session(self) -> Callable:
        """
        Returns a decorator that:
        - Creates a new AsyncSession per request.
        - Injects it as the last argument to the route handler.
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
                    try:
                        kwargs["session"] = session
                        return await run_sync_or_async(handler, *args, **kwargs)
                    except Exception:
                        await session.rollback()  # Rollback on error
                        raise  # Re-raise exception for proper error handling
                    finally:
                        #closes the active session
                        await session.close()
            return wrapper
        return decorator

async def create_tables(database: SqlDatabase) -> None:
    """
    Creates db tables with initilized SqlDatabase instance
    """
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Model.metadata.create_all)
