"""
UsersAPI dtos
"""
from typing import Optional, Any
from pydantic import BaseModel, Field, field_serializer

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
