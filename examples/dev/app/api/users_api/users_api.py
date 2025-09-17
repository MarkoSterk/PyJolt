"""
Users API
"""
from typing import Any, Optional

from pydantic import BaseModel, field_serializer, Field

from pyjolt import MediaType, Request, Response, HttpStatus, html_abort
from pyjolt.controller import (Controller, consumes, get, path, delete,
                               post, produces, Descriptor,
                               open_api_docs)

from app.api.models import User
from app.extensions import db

class TestModel(BaseModel):
    fullname: str = Field(min_length=3, max_length=15)
    age: int = Field(gt=17)
    email: str = Field(min_length=5, max_length=30)

class ResponseModel(BaseModel):
    message: str
    status: str
    data: Optional[Any] = None

    @field_serializer("data")
    def serialize_data(self, data: Any, _info):
        if isinstance(data, BaseModel):
            return data.model_dump()
        return data

class ErrorResponse(BaseModel):
    message: str
    status: int
    data: Optional[Any] = None

    @field_serializer("data")
    def serialize_data(self, data: Any, _info):
        if isinstance(data, BaseModel):
            return data.model_dump()
        return data

@path("/api/v1/users")
class UsersApi(Controller):

    @get("/", tags=["UsersAPI"])
    @produces(MediaType.APPLICATION_JSON)
    async def get_users(self, req: Request) -> Response[ResponseModel]:
        """Endpoint for returning all app users"""
        response: ResponseModel = ResponseModel(message="All users fetched.",
                                                status="success", data=None)
        return req.response.json(response).status(200)

    @get("/<int:user_id>")
    @produces(MediaType.APPLICATION_JSON)
    @open_api_docs(Descriptor(status=HttpStatus.NOT_FOUND, description="User not found", body=ErrorResponse),
                   Descriptor(status=HttpStatus.BAD_REQUEST, description="Bad request", body=ErrorResponse))
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

    @get("/hello")
    @produces(MediaType.TEXT_HTML)
    async def hello_user(self, req: Request) -> Response:
        """Hello world for user"""
        return (await req.response.html("index.html")).status(HttpStatus.CONFLICT)

    @post("/")
    @consumes(MediaType.APPLICATION_JSON)
    @produces(MediaType.APPLICATION_JSON)
    async def create_user(self, req: Request, data: TestModel) -> Response[ResponseModel]:
        """Consumes and produces json"""
        user: User = await User.query().filter_by(email=data.email).first()
        print("User: ", user)
        if user:
            return req.response.json({
                "message": "User with this email already exists",
                "status": "error"
            }).status(HttpStatus.BAD_REQUEST)
        user = User(email=data.email, fullname=data.fullname, age=data.age)
        session = db.create_session()
        session.add(user)
        await session.commit()

        return req.response.json({
            "message": "User added successfully",
            "status": "success"
        }).status(200)

    @delete("/<int:user_id>")
    @produces(media_type=MediaType.NO_CONTENT, status_code=HttpStatus.NO_CONTENT)
    async def delete_user(self, req: Request, user_id: int) -> Response:
        """Deletes user"""
        user: User = await User.query().filter_by(id=user_id).first()
        if not user:
            return req.response.json({
                "message": "User with this id does not exist",
                "status": "error"
            }).status(HttpStatus.NOT_FOUND)
        session = db.create_session()
        await session.delete(user)
        await session.commit()
        return req.response.no_content()
