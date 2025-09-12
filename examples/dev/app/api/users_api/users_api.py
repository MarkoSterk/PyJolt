"""
Users API
"""
from typing import Any
from pyjolt import Request, Response, MediaType
from pyjolt.controller import Controller, path, get, produces, consumes, post
from pydantic import BaseModel, field_serializer

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

@path("/<string:lang>/api/v1/users")
class UsersApi(Controller):

    @get("/")
    async def get_users(self, req: Request, lang: str) -> Response:
        """Endpoint for returning all app users"""
        return req.response.json({
            "message": "All users fetched",
            "status": "success",
            "data": None
        }).status(200)
    
    @get("/<int:user_id>")
    @produces(MediaType.APPLICATION_JSON)
    async def get_user(self, req: Request, lang: str, user_id: int) -> Response:
        """Returns single user by id"""
        return req.response.json({
            "message": "User fetched successfully",
            "status": "success",
            "data": {
                "url_for": self.app.url_for("Static.get", filename="board_test.jpg"),
                "user_id": user_id
            }
        }).status(200)
    
    @get("/hello")
    @produces(MediaType.TEXT_HTML)
    async def hello_user(self, req: Request, lang: str) -> Response:
        """Hello world for user"""
        return await req.res.html("index.html", {"language": lang})

    @post("/")
    @consumes(MediaType.APPLICATION_JSON)
    @produces(MediaType.APPLICATION_JSON)
    async def post_test(self, req: Request, lang: str, data: TestModel) -> Response[ResponseModel]:
        """Consumes json"""
        payload: ResponseModel = ResponseModel(message="Request was successful.", status="success", data=data)
        return req.response.json(payload).status(200)
