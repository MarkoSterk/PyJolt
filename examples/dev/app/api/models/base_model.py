"""
Base model
"""
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase
from typing import Type

from pyjolt.database.sql import create_declarative_base

Base: Type[DeclarativeBase] = create_declarative_base("db")

class BaseModel(Base):

    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)
