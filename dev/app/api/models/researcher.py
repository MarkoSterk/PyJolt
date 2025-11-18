"""Researcher model"""
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column
from pyjolt.admin import register_model

from .base_model import DatabaseModel

@register_model
class Researcher(DatabaseModel):
    """Researcher database model"""
    __tablename__ = "researchers"

    fullname: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    education: Mapped[str] = mapped_column(Text, nullable=True)
    employment: Mapped[str] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=True)
