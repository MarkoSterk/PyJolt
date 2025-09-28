"""
Authentication api
"""
from app.api.models import User
from app.authentication import auth
from app.extensions import db
from pydantic import BaseModel

from pyjolt import HttpStatus, MediaType, Request, Response
from pyjolt.controller import Controller, consumes, path, post, produces


class LoginData(BaseModel):

    email: str
    password: str


@path("/api/v1/auth")
class AuthApi(Controller):

    @post("/")
    @consumes(MediaType.APPLICATION_JSON)
    @produces(MediaType.APPLICATION_JSON)
    async def login(self, req: Request, data: LoginData) -> Response:
        session = db.create_session()
        user: User = await User.query(session).filter_by(email=data.email).first()
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
