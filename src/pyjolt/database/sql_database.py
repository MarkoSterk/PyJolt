"""
sql_database.py
Module for sql database connection/intergration
"""

#import asyncio
from typing import Optional, Callable, Any
from functools import wraps

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    AsyncSession,
)
from sqlalchemy.orm import sessionmaker

class SqlDatabase:
    """
    A simple async Database interface using SQLAlchemy.
    It handles:
      - engine creation
      - session creation
      - explicit commit
      - connect & disconnect (dispose)
    """

    class _BaseModel(DeclarativeBase):
        """
        Base model from sqlalchemy.orm
        """

    def __init__(self, app = None):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory = None
        self._session: Optional[AsyncSession] = None
        self._db_uri: str = None
        if app:
            self.init_app(app)

    def init_app(self, app) -> None:
        """
        Initilizes the database interface
        app.get_conf("DATABASE_URI") must returns a connection string like:
        "postgresql+asyncpg://user:pass@localhost/dbname"
        or "sqlite+aiosqlite:///./test.db"
        """
        self._db_uri = app.get_conf("DATABASE_URI")
        db_name: str = app.get_conf("DATABASE_NAME", False)
        if db_name is not False:
            self.__name__ = db_name
        app.add_extension(self)

    async def connect(self) -> None:
        """
        Creates the async engine and session factory, if not already created.
        Also creates a single AsyncSession instance you can reuse.
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

        if not self._session:
            # Create a session instance to be used throughout the app
            self._session = self._session_factory()

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

    async def disconnect(self) -> None:
        """
        Closes the active session and disposes of the engine.
        This should be called when your ASGI app shuts down.
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
    def Model(self) -> DeclarativeBase:
        """
        Returns base model for all model classes
        """
        return self._BaseModel

    @property
    def with_session(self) -> Callable:
        """
        Returns a decorator that:
        - Creates a new AsyncSession per request
        - Injects it as the last argument to the route handler
        - Rolls back if an unhandled error occurs
        - Closes the session automatically afterward
        """
        def decorator(handler) -> Callable:
            @wraps(handler)
            async def wrapper(*args, **kwargs):
                if not self._session_factory:
                    raise RuntimeError(
                        "Database is not connected. "
                        "Did you forget to call `await db.connect()`?"
                    )
                session = self._session_factory()
                try:
                    # Add `session` as the last positional argument
                    kwargs["session"] = session
                    return await handler(*args, **kwargs)
                except Exception:
                    # If something goes wrong, rollback
                    await session.rollback()
                    raise
                finally:
                    # Always close the session
                    await session.close()
            return wrapper
        return decorator

async def create_tables(database: SqlDatabase) -> None:
    """
    Creates db tables with initilized SqlDatabase instance
    """
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Model.metadata.create_all)
