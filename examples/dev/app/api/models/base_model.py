"""
Base model
"""
from sqlalchemy.orm import mapped_column, Mapped

from pyjolt.database import create_declerative_base

Base = create_declerative_base("db")

class BaseModel(Base):

    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)
