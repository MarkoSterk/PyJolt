"""
Base model
"""
from pyjolt.database import create_declerative_base
from sqlalchemy.orm import mapped_column, Mapped

Base = create_declerative_base()

class BaseModel(Base):

    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)