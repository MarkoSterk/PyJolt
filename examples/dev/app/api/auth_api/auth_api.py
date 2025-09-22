"""
Authentication api
"""
from pyjolt import Request, Response, MediaType, HttpStatus
from pyjolt.controller import Controller, path, post, consumes, produces
from pydantic import BaseModel

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

        return req.response.json({
            "message": "Login successful",
            "status": "success"
        }).status(HttpStatus.OK)
