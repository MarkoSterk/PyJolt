"""
Example data model
"""
from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped

from pyjolt.database import create_declerative_base

Base = create_declerative_base()

class Example(Base):
    """
    Example model
    """
    #table name in database; usually plural
    __tablename__: str = "examples"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
