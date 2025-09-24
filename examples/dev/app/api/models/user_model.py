"""
User models
"""
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.extensions import db

class User(db.Model):
    """
    User model
    """
    __tablename__: str = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    fullname: Mapped[str] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(50), unique=True)
    age: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String(100), nullable=True)

    roles: Mapped[list["Role"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        single_parent=True,
        lazy="immediate"
    )

class Role(db.Model):
    """
    User role
    """
    __tablename__: str = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(20))
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    user: Mapped["User"] = relationship(back_populates="roles") 
