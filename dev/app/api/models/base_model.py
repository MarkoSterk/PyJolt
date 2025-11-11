"""
Base database model
"""
from typing import Type
from datetime import datetime, timezone
from pyjolt.database.sql import create_declarative_base, DeclarativeBaseModel
from sqlalchemy import DateTime
from sqlalchemy.orm import mapped_column, Mapped

Base: Type[DeclarativeBaseModel] = create_declarative_base() #type: ignore[misc,valid-type]

class DatabaseModel(Base):#type: ignore[misc,valid-type]
    """Base for all database models"""

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=lambda: datetime.now(timezone.utc),
                                                nullable=False)
