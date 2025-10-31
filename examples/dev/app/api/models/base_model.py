"""
Base model
"""
from typing import Type
from sqlalchemy.orm import mapped_column, Mapped

from pyjolt.database.sql import create_declarative_base, DeclarativeBaseModel

Base: Type[DeclarativeBaseModel] = create_declarative_base("db")

class BaseModel(Base):

    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)
