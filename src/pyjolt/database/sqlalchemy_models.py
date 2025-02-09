"""
Base model classes for SQLAlchemy models.
"""
import logging
from typing import Any, Type, Callable, TypeVar, Dict
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import Select

def create_declerative_base() -> Type:
    """
    Declerative base class factory.
    Used by the SqlDatabase instance to create a base model for all
    data models. Makes sure multiple instances of the SqlDatabase
    class (used for multiple databases) don't cross-contaminate the
    session_factory method
    """

    base = declarative_base()

    class DeclarativeBase(base):
        """
        Base model from sqlalchemy.orm with
        query classmethod
        """
        __abstract__ = True

        @classmethod
        def add_session_factory(cls, factory: Callable):
            """
            Ads session factory to class
            Called by the SqlDatabase instance at initilization
            """
            cls._session_factory = factory

        @classmethod
        def query(cls, session: AsyncSession = None) -> "AsyncQuery":
            """
            Query class method. Returns an AsyncQuery class instance with a session
            the model class.

            Allows for intuitive querying on model classes. Handles rollback if
            an error occurs. If using this interface it is no longer neccessary to
            use the @db.with_session decorator. However, the decorator approach is
            advised if performing multiple queries in a single route handler/method
            because this way only a single session is used instead of multiple.
            """
            use_session_factory: bool = session is not None
            if session is None:
                if cls._session_factory is None:
                    raise RuntimeError(f"Session factory is not set on model {cls}")
                session: AsyncSession = cls._session_factory()
            return AsyncQuery(session, cls, use_session_factory)
    return DeclarativeBase

#pylint: disable-next=C0103
_T0 = TypeVar("_T0", bound=Any)

class AsyncQuery:
    """
    Async-friendly intuitive query object.
    Easy and intuitive querying with pagination support.
    """

    def __init__(self, session: AsyncSession, model: Type[_T0], use_session_factory: bool):
        self.session = session
        self.model = model
        self.use_session_factory = use_session_factory
        self._query: Select = select(model)  # Start with SELECT * FROM table

    def where(self, *conditions) -> "AsyncQuery":
        """Adds WHERE conditions (same as `filter()`)."""
        return self.filter(*conditions)

    def filter(self, *conditions) -> "AsyncQuery":
        """Adds WHERE conditions to the query (supports multiple conditions)."""
        self._query = self._query.filter(*conditions)
        return self

    def filter_by(self, **kwargs) -> "AsyncQuery":
        """Adds WHERE conditions using keyword arguments (simpler syntax)."""
        self._query = self._query.filter_by(**kwargs)
        return self

    def join(self, other_model: Type[_T0]) -> "AsyncQuery":
        """Performs a SQL JOIN with another model."""
        self._query = self._query.join(other_model)
        return self

    def limit(self, num: int) -> "AsyncQuery":
        """Limits the number of results returned."""
        self._query = self._query.limit(num)
        return self

    def offset(self, num: int) -> "AsyncQuery":
        """Skips a certain number of results (used for pagination)."""
        self._query = self._query.offset(num)
        return self

    def order_by(self, *columns) -> "AsyncQuery":
        """Sorts results based on one or more columns."""
        self._query = self._query.order_by(*columns)
        return self

    async def count(self) -> int:
        """
        Returns the total number of records matching the current query,
        preserving any applied filters.
        """
        count_query = select(func.count()).select_from(self.model)
        # Apply existing filters
        if hasattr(self._query, "whereclause") and self._query.whereclause is not None:
            count_query = count_query.where(self._query.whereclause)

        result = await self.session.execute(count_query)
        return result.scalar() or 0

    async def paginate(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Paginates results.
        page (int): The page number (1-based index).
        per_page (int): Number of results per page.

        Returns:
            dict: {
                "items": List of results,
                "total": Total records,
                "page": Current page,
                "pages": Total pages,
                "per_page": Results per page,
                "has_next": Whether there's a next page,
                "has_prev": Whether there's a previous page
            }
        """
        page = max(page, 1)

        total_records = await self.count()
        total_pages = (total_records + per_page - 1) // per_page  # Round up division

        self._query = self._query.limit(per_page).offset((page - 1) * per_page)
        result = await self._execute_query()
        items = result.scalars().all()

        return {
            "items": items,
            "total": total_records,
            "page": page,
            "pages": total_pages,
            "per_page": per_page,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }

    async def _execute_query(self):
        """Executes the query safely with automatic rollback on failure."""
        try:
            result = await self.session.execute(self._query)
            return result
        except SQLAlchemyError as e:
            if self.use_session_factory:
                await self.session.rollback()
            logging.error("Database query failed: %s", e)
            raise
        finally:
            if self.use_session_factory:
                await self.session.close()

    async def all(self) -> list:
        """Executes the query and returns all results."""
        result = await self._execute_query()
        return result.scalars().all()

    async def first(self) -> Any:
        """Executes the query and returns the first result."""
        result = await self._execute_query()
        return result.scalars().first()

    async def one(self) -> Any:
        """Executes the query and expects exactly one result."""
        result = await self._execute_query()
        return result.scalars().one()

