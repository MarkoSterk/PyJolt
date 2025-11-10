"""
Helpers and constants for admin dashboard
"""
from enum import StrEnum

class FormType(StrEnum):
    CREATE = "create"
    EDIT = "edit"

class PermissionType(StrEnum):
    CAN_ENTER = "enter"
    CAN_VIEW = "view"
    CAN_CREATE = "create"
    CAN_EDIT = "edit"
    CAN_DELETE = "delete"
