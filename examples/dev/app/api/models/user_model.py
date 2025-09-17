"""
User models
"""

from app.extensions import db
from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column, Mapped

class User(db.Model):
    """
    User model
    """
    __tablename__: str = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    fullname: Mapped[str] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(50), unique=True)
    age: Mapped[int] = mapped_column(Integer)
