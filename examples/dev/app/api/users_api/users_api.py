"""
Users API
"""
from app.api.models import Role, User
from app.api.users_api.dtos import ErrorResponse, ResponseModel, TestModel
from app.authentication import UserRoles
from app.extensions import db

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
from pyjolt.database import AsyncSession


@path("/api/v1/users", tags=["Users"])
class UsersApi(Controller):

    @get("/")
    @produces(MediaType.APPLICATION_JSON)
    @db.managed_session
    async def get_users(self, req: Request, session: AsyncSession) -> Response[ResponseModel]:
        """Endpoint for returning all app users"""
        #await asyncio.sleep(10)
        users = await User.query(session).all()
        response: ResponseModel = ResponseModel(message="All users fetched.",
                                                status="success", data=None)
        return req.response.json(response).status(HttpStatus.OK)

    @get("/<int:user_id>")
    @produces(MediaType.APPLICATION_JSON)
    @open_api_docs(
        Descriptor(status=HttpStatus.NOT_FOUND, description="User not found", body=ErrorResponse),
        Descriptor(status=HttpStatus.BAD_REQUEST, description="Bad request", body=ErrorResponse),
        Descriptor(status=HttpStatus.CONFLICT, description="Conflict response",
                   media_type=MediaType.TEXT_HTML))
    async def get_user(self, req: Request, user_id: int) -> Response[ResponseModel]:
        """Returns single user by id"""
        if user_id > 10:
            return html_abort("index.html", HttpStatus.CONFLICT)
        return req.response.json({
            "message": "User fetched successfully",
            "status": "success",
            "data": {
                "url_for": self.app.url_for("Static.get", filename="board_test.jpg"),
                "user_id": user_id
            }
        }).status(HttpStatus.OK)

    @post("/")
    @consumes(MediaType.APPLICATION_JSON)
    @produces(MediaType.APPLICATION_JSON)
    async def create_user(self, req: Request, data: TestModel) -> Response[ResponseModel]:
        """Consumes and produces json"""
        session = db.create_session()
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
        await session.commit()
        await session.close() #must close the session
        return req.response.json({
            "message": "User added successfully",
            "status": "success"
        }).status(200)

    @delete("/<int:user_id>")
    @produces(media_type=MediaType.NO_CONTENT, status_code=HttpStatus.NO_CONTENT)
    async def delete_user(self, req: Request, user_id: int) -> Response:
        """Deletes user"""
        session = db.create_session()
        user: User = await User.query(session).filter_by(id=user_id).first()
        if not user:
            return req.response.json({
                "message": "User with this id does not exist",
                "status": "error"
            }).status(HttpStatus.NOT_FOUND)

        await session.delete(user)
        await session.commit()
        return req.response.no_content()
