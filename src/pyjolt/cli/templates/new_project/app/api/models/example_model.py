"""
Example data model
"""
from app.extensions import db
from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column, Mapped

class Example(db.Model):
    """
    Example model
    """
    #table name in database; usually plural
    __tablename__: str = "examples"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
