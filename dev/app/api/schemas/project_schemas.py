"""Project related schemas"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING, Self
from pydantic import BaseModel

from .base_schema import QueryResponseSchema, BaseResponse

if TYPE_CHECKING:
    from app.api.models.project import Project

class ProjectQuerySchema(BaseModel):
    """Schema for project queries"""
    title_slv: Optional[str] = None
    title_eng: Optional[str] = None
    keywords_slv: Optional[str] = None
    keywords_eng: Optional[str] = None
    leader: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    researchers: Optional[str] = None

    page: int = 1
    per_page: int = 10

class ProjectOutSchema(BaseModel):
    """Project out schema"""

    id: int
    title_slv: Optional[str] = None
    title_eng: Optional[str] = None
    code: Optional[str] = None
    abstract_slv: Optional[str] = None
    abstract_eng: Optional[str] = None
    keywords_slv: Optional[str] = None
    keywords_eng: Optional[str] = None
    leader: Optional[str] = None
    duration: Optional[str] = None
    researchers: Optional[str] = None

    @classmethod
    def from_model(cls, project: "Project") -> Self:
        """Creates schema from project model"""
        return cls(
            id=project.id,
            code=project.code,
            title_slv=project.title_slv,
            title_eng=project.title_eng,
            abstract_slv=project.abstract_slv,
            abstract_eng=project.abstract_eng,
            keywords_slv=project.keywords_slv,
            keywords_eng=project.keywords_eng,
            leader=project.leader,
            duration=project.duration,
            researchers=project.researchers
        )

class ProjectResponseSchema(BaseResponse):
    """Project response schema"""
    data: ProjectOutSchema

class ProjectsQueryDataSchema(QueryResponseSchema):
    """Publication API base query response"""
    items: list[ProjectOutSchema]

class ProjectsQueryResponseSchema(BaseResponse):
    """Publications API query response"""
    data: ProjectsQueryDataSchema
