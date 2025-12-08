"""Researcher model"""
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column
from pyjolt.admin import register_model

from .base_model import OtherDatabaseModel

@register_model
class Dummy(OtherDatabaseModel):
    """Researcher database model"""
    __tablename__ = "dummies"

    fullname: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=True)
