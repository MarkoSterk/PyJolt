"""
Authentication API
"""
from typing import cast
from pyjolt import Response, Request, HttpStatus, MediaType, abort
from pyjolt.controller import (Controller, path, get, post,
                               consumes, produces, open_api_docs,
                               Descriptor)
from pyjolt.database.sql import AsyncSession
from pyjolt.auth import login_required, AuthUtils

from app.api.models.user import User
from app.api.schemas.base_schema import ErrorResponseSchema, BaseResponse
from app.api.schemas.user_schemas import UserOutSchema, LoginSchema, LoginOutSchema
from app.extensions import db

@path("/api/v1/auth")
class AuthApi(Controller):
    """
    Authentication controller
    """

    @get("/current")
    @produces(MediaType.APPLICATION_JSON)
    @open_api_docs(Descriptor(status=HttpStatus.FORBIDDEN,
                              description="Not logged in",
                              body=ErrorResponseSchema))
    @login_required
    async def current_user(self, req: Request) -> Response[LoginOutSchema]:
        """Returns current authenticated user"""
        return req.res.json({
            "message": "User is authenticated",
            "status": "success",
            "data": UserOutSchema(
            id=req.user.id,
            fullname=req.user.fullname,
            email=req.user.email
        )}).status(HttpStatus.OK)

    @post("/admin", open_api_spec=False)
    @consumes(MediaType.APPLICATION_X_WWW_FORM_URLENCODED)
    @produces(MediaType.APPLICATION_JSON)
    async def login_form(self, req: Request,
                         login_data: LoginSchema) -> Response[LoginOutSchema]:
        """Login for admin dashboard"""
        print("Login data: ", login_data.model_dump())
        return await self.login_user(req, login_data)

    @post("/login")
    @consumes(MediaType.APPLICATION_JSON)
    @produces(MediaType.APPLICATION_JSON)
    @open_api_docs(Descriptor(status=HttpStatus.BAD_REQUEST,
                              description="Wrong credentials",
                              body=ErrorResponseSchema))
    async def login(self, req: Request,
                    login_data: LoginSchema) -> Response[LoginOutSchema]:
        """Login route"""
        return await self.login_user(req, login_data)

    @get("/logout")
    @produces(MediaType.APPLICATION_JSON)
    @open_api_docs(Descriptor(status=HttpStatus.FORBIDDEN,
                              description="Must be logged in",
                              body=ErrorResponseSchema))
    @login_required
    async def logout(self, req: Request) -> Response[BaseResponse]:
        """User logout"""
        req.res.set_cookie(cookie_name=self.app.get_conf("COOKIE_NAME"),
                           value="",
                           max_age=0,
                           http_only=True)
        return req.res.json({
            "message": "Logout successful",
            "status": "success"
        }).status(HttpStatus.OK)

    @db.readonly_session
    async def login_user(self, req: Request,
                         login_data: LoginSchema,
                         session: AsyncSession = cast(AsyncSession, None)):
        """User login"""
        user: User = await User.query(session).filter_by(email=login_data.email).first()
        if user is None:
            abort(msg="Wrong credentials.", status_code=HttpStatus.BAD_REQUEST)

        valid_pass: bool = AuthUtils.check_password_hash(login_data.password, user.password)
        if valid_pass is False:
            abort(msg="Wrong credentials", status_code=HttpStatus.BAD_REQUEST)
        secret_key: str = self.app.get_conf("SECRET_KEY")
        cookie: str = AuthUtils.create_signed_cookie_value(user.id, secret_key)
        req.res.set_cookie(cookie_name=self.app.get_conf("COOKIE_NAME"),
                           value=cookie,
                           max_age=self.app.get_conf("COOKIE_DURATION"),
                           http_only=True)
        self.app.logger.info(f"User: {user.fullname}(id={user.id}) logged in.")

        return req.res.json({
            "message": "Login successful",
            "status": "success",
            "data": UserOutSchema(id=user.id,fullname=user.fullname,email=user.email)
        }).status(HttpStatus.OK)
