"""
Publication schemas
"""
from datetime import datetime
from typing import Optional, Self, TYPE_CHECKING
from pydantic import BaseModel, Field, field_serializer
from .base_schema import BaseResponse, QueryResponseSchema

if TYPE_CHECKING:
    from ..models.publication import Publication

class PublicationsQuerySchema(BaseModel):
    """Schema for publication querying"""
    title: Optional[str] = Field(None, description="Title or part of title")
    pub_type: Optional[str] = Field(None, description="Type of publication")
    publisher: Optional[str] = Field(None, description="Publication publisher")
    container_title: Optional[str] = Field(None, description="Journal/Book title")
    date_published: datetime = Field(datetime.fromisoformat("2000-01-01"),
                                description="Date of publication")
    page: int = Field(1, description="Page of query results")
    per_page: int = Field(10, description="Results per page")

class PublicationOutSchema(BaseModel):
    """Publication out schema"""
    doi: str
    authors: list[str]
    title: str
    pub_type: str
    publisher: str
    container_title: str
    page: Optional[str] = None
    volume: Optional[str] = None
    date_published: Optional[datetime] = None
    abstract: Optional[str] = None

    @field_serializer('date_published')
    def serialize_date_published(self, dt: datetime, _info):
        """Serialized date_published to ISO string"""
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    @classmethod
    def from_model(cls, model: "Publication") -> Self:
        """Creates schema from model"""
        return cls(
            doi=model.doi,
            authors=model.authors,
            title=model.title,
            pub_type=model.pub_type,
            publisher=model.publisher,
            container_title=model.container_title,
            page=model.page,
            volume=model.volume,
            date_published=model.date_published,
            abstract=model.abstract
        )

class PublicationResponseSchema(BaseResponse):
    """Publications API response schema"""
    data: PublicationOutSchema

class PublicationsQueryDataSchema(QueryResponseSchema):
    """Publication API base query response"""
    items: list[PublicationOutSchema]

class PublicationsQueryResponseSchema(BaseResponse):
    """Publications API query response"""
    data: PublicationsQueryDataSchema
