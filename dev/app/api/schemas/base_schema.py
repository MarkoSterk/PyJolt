"""
Base response model
"""
from typing import Optional
from pydantic import BaseModel, Field

class BaseResponse(BaseModel):
    """Base"""
    message: Optional[str] = Field("Request successful")
    status: Optional[str] = Field("success")
    data: Optional[BaseModel] = Field(None, description="Data payload - a pydantic object")

class ErrorResponseSchema(BaseModel):
    """Generic error response schema"""
    message: str
    status: str
    data: Optional[dict] = None

class QueryResponseSchema(BaseModel):
    """Query response schema"""
    items: list[BaseModel]
    total: int
    page: int
    pages: int
    per_page: int
    has_next: bool
    has_prev: bool
