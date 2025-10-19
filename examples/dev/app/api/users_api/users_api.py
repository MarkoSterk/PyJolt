"""
Users API
"""
from app.api.models import Role, User
from app.api.users_api.dtos import ErrorResponse, TestModel, TestModelOut, TestModelOutList
from app.authentication import UserRoles
from app.extensions import db, cache

import asyncio
from pyjolt import HttpStatus, MediaType, Request, Response, html_abort
from pyjolt.controller import (
    Controller,
    Descriptor,
    consumes,
    delete,
    get,
    open_api_docs,
    path,
    post,
    produces
)
from pyjolt.database.sql import AsyncSession

@path("/api/v1/users", tags=["Users"])
class UsersApi(Controller):

    @get("/")
    @produces(MediaType.APPLICATION_JSON)
    @db.managed_session
    async def get_users(self, req: Request, session: AsyncSession) -> Response[TestModelOutList]:
        """Endpoint for returning all app users"""
        #await asyncio.sleep(10) #for cache testing - if response is cached the endpoint returns immediately. Otherwise it takes 10 seconds to respond
        users = await User.query(session).all()
        response = {
            "message": "Users fetched successfully",
            "status": "success",
            "data": [TestModel(fullname=user.fullname, age=user.age, email=user.email) for user in users] if users else None
        }
        return req.response.json(response).status(HttpStatus.OK)

    @get("/<int:user_id>")
    @produces(MediaType.APPLICATION_JSON)
    @open_api_docs(
        Descriptor(status=HttpStatus.NOT_FOUND, description="User not found", body=ErrorResponse),
        Descriptor(status=HttpStatus.BAD_REQUEST, description="Bad request", body=ErrorResponse))
    async def get_user(self, req: Request, user_id: int) -> Response[TestModelOut]:
        """Returns single user by id"""
        if user_id > 10:
            return html_abort("index.html", HttpStatus.CONFLICT)
        await asyncio.sleep(10)
        return req.response.json({
            "message": "User fetched successfully",
            "status": "success",
            "data": TestModel(fullname="Marko Šterk", age=22, email="marko_sterk@hotmail.com")
        }).status(HttpStatus.OK)

    @post("/")
    @consumes(MediaType.APPLICATION_JSON)
    @produces(MediaType.APPLICATION_JSON)
    @db.managed_session
    async def create_user(self, req: Request, data: TestModel, session: AsyncSession) -> Response[TestModelOut]:
        """Consumes and produces json"""
        user: User = await User.query(session).filter_by(email=data.email).first()
        if user:
            return req.response.json({
                "message": "User with this email already exists",
                "status": "error"
            }).status(HttpStatus.BAD_REQUEST)
        user = User(email=data.email, fullname=data.fullname, age=data.age)
        session.add(user)
        await session.flush()
        role = Role(user_id=user.id, role=UserRoles.ADMIN)
        session.add(role)
        return req.response.json({
            "message": "User added successfully",
            "status": "success"
        }).status(200)

    @delete("/<int:user_id>")
    @produces(media_type=MediaType.NO_CONTENT, status_code=HttpStatus.NO_CONTENT)
    @open_api_docs(
        Descriptor(status=HttpStatus.NOT_FOUND, description="User not found", body=ErrorResponse
    ))
    @db.managed_session
    async def delete_user(self, req: Request, user_id: int, session: AsyncSession) -> Response:
        """Deletes user"""
        user: User = await User.query(session).filter_by(id=user_id).first()
        if not user:
            return req.response.json({
                "message": "User with this id does not exist",
                "status": "error"
            }).status(HttpStatus.NOT_FOUND)

        await session.delete(user)
        return req.response.no_content()
