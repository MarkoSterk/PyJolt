"""Authentication middleware"""
from typing import Any, cast
from pyjolt.auth import Authentication, AuthUtils
from pyjolt import Request
from pyjolt.database.sql import AsyncSession
from app.extensions import db
from app.api.models.user import User

class AuthMW(Authentication):
    """Middleware implementation"""

    configs_name: str = "AUTH_MW"

    async def user_loader(self, req: Request) -> Any:
        """Loads user from the provided cookie"""
        secret_key: str = cast(str, self.app.get_conf("SECRET_KEY"))
        cookie_header = req.headers.get("cookie", "")
        if cookie_header:
            # Split the cookie string on semicolons and equals signs to extract individual cookies
            cookies = dict(cookie.strip().split('=', 1) for cookie in cookie_header.split(';'))
            auth_cookie = cookies.get(self.app.get_conf("COOKIE_NAME"))
            if auth_cookie:
                user_id = AuthUtils.decode_signed_cookie(auth_cookie, secret_key)
                if user_id:
                    return await self.get_user(user_id, session=cast(AsyncSession,None))
        return None

    @db.readonly_session
    async def get_user(self, user_id, session: AsyncSession) -> Any:
        """Loads the user"""
        return await User.query(session).filter_by(id=user_id).first()

    async def role_check(self, user: Any, roles: list[Any]) -> bool:
        return False
