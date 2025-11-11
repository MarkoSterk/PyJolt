"""Schemas for researcher model"""
from typing import Optional, TYPE_CHECKING, Self
from pydantic import BaseModel

from .base_schema import BaseResponse

if TYPE_CHECKING:
    from app.api.models.researcher import Researcher

class ResearcherOutSchema(BaseModel):
    """Researcher output schema"""
    id: int
    fullname: str
    code: str
    email: str
    education: Optional[str] = None
    employment: Optional[str] = None
    title: Optional[str] = None

    @classmethod
    def from_model(cls, researcher: "Researcher") -> Self:
        """Creates a schema from model"""
        return cls(
            id=researcher.id,
            fullname=researcher.fullname,
            code=researcher.code,
            email=researcher.email,
            education=researcher.education,
            employment=researcher.employment,
            title=researcher.title
        )

class ResearcherResponseSchema(BaseResponse):
    """Researcher response schema"""
    data: ResearcherOutSchema

class AllResearchersResponseSchema(BaseResponse):
    """All researchers out schema"""
    data: list[ResearcherOutSchema]
