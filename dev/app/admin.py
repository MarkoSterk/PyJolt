"""Admin dashboard extension"""
from typing import Type
from pyjolt import Request
from pyjolt.admin import AdminDashboard
from pyjolt.caching.cache import Cache
from pyjolt.email import EmailClient
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

    async def has_cache_permission(self, req: Request, cache: Cache) -> bool:
        return True

    async def email_recipient_query(self, req: Request, query: str, client: EmailClient) -> list[tuple[str, str]]:
        """
        Email recipient query implementation
        """
        return [
            ("Marko Šterk", "marko.sterk@izum.si"),
            ("Andrej Korošec", "andrej.korosec@izum.si"),
            ("Andrej Zidarič", "andrej.zidaric@izum.si"),
            ("Janja Zorman", "janja.zorman@izum.si"),
            ("Filip Pasarič", "filip.pasaric@izum.si")
        ]
    
    async def has_files_permission(self, req):
        return True

admin_extension: AdminExtension = AdminExtension()
