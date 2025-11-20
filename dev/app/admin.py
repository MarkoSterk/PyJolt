"""Admin dashboard extension"""
from typing import Type
from pyjolt import Request
from pyjolt.admin import AdminDashboard
from pyjolt.database.sql.declarative_base import DeclarativeBaseModel

class AdminExtension(AdminDashboard):
    """Admin dashboard extension"""

    async def has_enter_permission(self, req: Request) -> bool:
        return True

    async def has_create_permission(self, req: Request, model: Type[DeclarativeBaseModel]) -> bool:
        return True

    async def has_delete_permission(self, req: Request, model: Type[DeclarativeBaseModel]) -> bool:
        return True

    async def has_update_permission(self, req: Request, model: Type[DeclarativeBaseModel]) -> bool:
        return True

    async def has_view_permission(self, req: Request, model: Type[DeclarativeBaseModel]) -> bool:
        return True

admin_extension: AdminExtension = AdminExtension()
