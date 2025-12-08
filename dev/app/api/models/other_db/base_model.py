"""
Base database model
"""
from datetime import datetime, timezone
from pyjolt.database.sql import DeclarativeBaseModel
from sqlalchemy import DateTime
from sqlalchemy.orm import mapped_column, Mapped

class OtherDatabaseModel(DeclarativeBaseModel):
    """Base for all database models"""

    __abstract__ = True
    __db_name__ = "other_db"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=lambda: datetime.now(timezone.utc),
                                                nullable=False)
    
    class Meta(DeclarativeBaseModel.Meta):
        pass
