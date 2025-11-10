"""
Helpers and constants for admin dashboard
"""
from typing import Type
from enum import StrEnum
from sqlalchemy.inspection import inspect
from ..database.sql.base_protocol import DeclarativeBaseModel

class FormType(StrEnum):
    CREATE = "create"
    EDIT = "edit"

class PermissionType(StrEnum):
    CAN_ENTER = "enter"
    CAN_VIEW = "view"
    CAN_CREATE = "create"
    CAN_EDIT = "edit"
    CAN_DELETE = "delete"

EXCLUDE_COLUMNS: list[str] = ["password", "pass", "hash"]

def extract_table_columns(Model: Type[DeclarativeBaseModel], limit: int = 8):
    """
    Extracts SQLAlchemy model columns suitable for displaying in a generic table.

    Rules:
      - Always include the primary key column(s) first.
      - Then include up to (limit - number_of_pk) additional columns
        sorted alphabetically by their attribute name.
      - Primary key(s) always appear first, even if alphabetically later.

    Args:
        Model: SQLAlchemy declarative model class.
        limit (int): Maximum number of columns to include (default = 8).

    Returns:
        list[Column]: Ordered list of SQLAlchemy Column objects.
    """
    mapper = inspect(Model)
    cols = list(mapper.columns)

    pk_keys = [c.key for c in cols if c.primary_key]
    non_pk_keys = sorted([c.key for c in cols if not c.primary_key and c.key.lower() not in EXCLUDE_COLUMNS], key=str.lower)

    take = max(0, limit - len(pk_keys))
    return pk_keys + non_pk_keys[:take]
