"""
Authentication api
"""
from pyjolt import Request, Response, MediaType, HttpStatus
from pyjolt.controller import Controller, path, post, consumes, produces
from pydantic import BaseModel

from app.api.models import User
from app.authentication import auth

class LoginData(BaseModel):

    email: str
    password: str


@path("/api/v1/auth")
class AuthApi(Controller):

    @post("/")
    @consumes(MediaType.APPLICATION_JSON)
    @produces(MediaType.APPLICATION_JSON)
    async def login(self, req: Request, data: LoginData) -> Response:
        user: User = await User.query().filter_by(email=data.email).first()
        if user is None:
            return req.response.json({
                "message": "Wrong credentials",
                "status": "error"
            }).status(HttpStatus.FORBIDDEN)
        cookie: str = auth.create_signed_cookie_value(user.id)
        req.response.set_cookie("auth_cookie", cookie, 86400, http_only=True)
        return req.response.json({
            "message": "Login successful",
            "status": "success"
        }).status(HttpStatus.OK)
