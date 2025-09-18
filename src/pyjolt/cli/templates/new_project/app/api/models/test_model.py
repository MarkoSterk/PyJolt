"""
Test data model
"""
from app.extensions import db
from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column, Mapped

class Test(db.Model):
    """
    Test model
    """
    #table name in database; usually plural
    __tablename__: str = "tests"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
