"""
Authentication
"""
from enum import StrEnum
from typing import override
from pyjolt.auth import Authentication

class UserRoles(StrEnum):
    ADMIN = "admin"
    SUPERUSER = "superuser"
    USER = "user"

class Auth(Authentication):

    @override
    async def user_loader(self, req):
        return {"name": "Marko", "lastname": "Šterk", "role": UserRoles.USER}

    @override
    async def role_check(self, user, roles) -> bool:
        return user["role"] in roles
