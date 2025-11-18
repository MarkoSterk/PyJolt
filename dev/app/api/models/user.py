"""
Application user model
"""
from typing import List, TYPE_CHECKING
from sqlalchemy.orm import mapped_column, Mapped, relationship
from pyjolt.admin import register_model

from .base_model import DatabaseModel

if TYPE_CHECKING:
    from .post import Post

@register_model
class User(DatabaseModel):
    """
    User object
    """
    __tablename__ = "users"
    fullname: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)

    password: Mapped[str] = mapped_column(nullable=False)

    posts: Mapped[List["Post"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
