"""
AI interface chat session model
"""
from sqlalchemy.orm import mapped_column, Mapped

from app.extensions import db

class ChatSession(db.Model):

    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
