"""
Test api endpoint
"""
from typing import Any
from pyjolt import Request, Response, HttpStatus, MediaType, abort
from pyjolt.controller import Controller, path, get, post, consumes, produces
from pydantic import BaseModel, field_serializer

from app.extensions import db
from app.api.models import Test

class CreateTest(BaseModel):
    name: str

class TestOut(CreateTest):
    id: int

    @classmethod
    def from_model(cls, model: Test):
        return cls(id=model.id, name=model.name)

class ResponseModel(BaseModel):
    message: str
    data: Any|None = None

    @field_serializer("data")
    def serialize_data(self, data: Any, _info):
        if isinstance(data, BaseModel):
            return data.model_dump()
        return data

@path("/api/v1/tests")
class TestApi(Controller):

    @get("/<int:test_id>")
    @produces(MediaType.APPLICATION_JSON)
    async def get_test(self, req: Request, test_id: int) -> Response[ResponseModel]:
        #The request object is always injected into the endpoint as the first argument
        #All other data (route parameters, indicated data objects etc) are injected
        #in the order of top->bottom, left->right

        test: Test = await Test.query().filter_by(id=test_id).first()
        if test is None:
            abort(f"Test with id {test_id} does not exist.", HttpStatus.NOT_FOUND, "error")

        return req.response.json({
            "message": "Test fetched successfully",
            "data": TestOut.from_model(test)
        }).status(HttpStatus.OK)
    
    @post("/")
    @consumes(MediaType.APPLICATION_JSON)
    @produces(MediaType.APPLICATION_JSON)
    async def create_test(self, req: Request, data: CreateTest) -> Response[CreateTest]:
        #CreateTest data is validated and injected into the endpoint controlelr
        #Some logic for creating/storing the test object data
        #Response data is serialized as the indicated CreateTest pydantic model in the response type
        #-> Response[CreateTest] indicates what type the response body is
        test: Test = Test(name=data.name)
        session = db.create_session()
        session.add(test)
        await session.commit()
        return req.response.json({
            "name": data.name
        }).status(HttpStatus.CREATED)
