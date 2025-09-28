"""
AI interface chat session model
"""
from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped

from .base_model import BaseModel

class ChatSession(BaseModel):

    __tablename__ = "chat_sessions"

    owner: Mapped[str] = mapped_column(String(20))
