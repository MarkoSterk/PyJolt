"""
Users API
"""
from typing import Any

from pydantic import BaseModel, field_serializer

from pyjolt import MediaType, Request, Response, abort, HttpStatus, html_abort
from pyjolt.controller import (Controller, consumes, get, path, delete,
                               post, produces, Descriptor,
                               open_api_docs)

from ..exceptions.custom_exceptions import EntityNotFound

class TestModel(BaseModel):
    name: str

class ResponseModel(BaseModel):
    message: str
    status: str
    data: Any|None

    @field_serializer("data")
    def serialize_data(self, data: Any, _info):
        if isinstance(data, BaseModel):
            return data.model_dump()
        return data

class ErrorResponse(BaseModel):
    message: str
    status: int
    data: Any|None

@path("/api/v1/users")
class UsersApi(Controller):

    @get("/")
    @produces(MediaType.APPLICATION_JSON)
    async def get_users(self, req: Request) -> Response[ResponseModel]:
        """Endpoint for returning all app users"""
        response: ResponseModel = ResponseModel(message="All users fetched.",
                                                status="success", data=None)
        return req.response.json(response).status(200)

    @get("/<int:user_id>")
    @produces(MediaType.APPLICATION_JSON)
    @open_api_docs(Descriptor(status=404, description="User not found", body=ErrorResponse),
                   Descriptor(status=400, description="Bad request", body=ErrorResponse))
    async def get_user(self, req: Request, user_id: int) -> Response[ResponseModel]:
        """Returns single user by id"""
        if user_id > 10:
            #raise EntityNotFound(f"User with id {user_id} not found")
            #return abort("Not found...", HttpStatus.NOT_FOUND)
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
    async def post_test(self, req: Request, data: TestModel) -> Response[ResponseModel]:
        """Consumes and produces json"""
        payload: ResponseModel = ResponseModel(message="Request was successful.",
                                               status="success", data=data)
        return req.response.json(payload).status(200)

    @delete("/<int:user_id>")
    async def delete_user(self, req: Request, user_id: int) -> Response:
        """Deletes user"""
        print("Deleting user: ", user_id)
        return req.response.no_content()
