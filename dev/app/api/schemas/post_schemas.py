"""
Post schemas
"""
from typing import List, Optional, Type, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import or_, func, literal
from pydantic import BaseModel, field_validator, Field

from .base_schema import BaseResponse, QueryResponseSchema

if TYPE_CHECKING:
    from app.api.models.post import Post

def any_tag_in_csv_condition(tags: list[str], post: "Type[Post]"):
    """Creates a func for searching for tags"""
    # Build: ',' || lower(tags_list) || ',' LIKE '%,tag,%' OR ...
    csv = literal(",") + func.lower(post.tags_list) + literal(",")
    patterns = [f"%,{t.strip().lower()},%" for t in tags if t and t.strip()]
    return or_(*[csv.like(p) for p in patterns]) if patterns else literal(True)

class PostsQuery(BaseModel):
    """Query schema for posts"""
    user_id: Optional[int] = Field(None, description="Authors id")
    active: bool = Field(True, description="Status of post")
    created_at: datetime = Field(datetime.fromisoformat("2025-10-01"),
                                           description="Date of creation")
    tags: Optional[List[str]] = Field(None, description="Tags of the post")
    page: int = Field(1, description="Page of query results")
    per_page: int = Field(10, description="Results per page")


    @field_validator("tags", mode="before")
    @classmethod
    def split_comma_string(cls, v):
        """Transforms comma separated string to list"""
        if isinstance(v, str):
            # Split on commas, strip whitespace, and remove empty entries
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

class PostUpdateInSchema(BaseModel):
    """Schema for updating post"""
    title_eng: Optional[str] = None
    title_slv: Optional[str] = None
    slug: Optional[str] = None
    content_eng: Optional[str] = None
    content_slv: Optional[str] = None
    tags: Optional[List[str]] = None

    @field_validator("tags", mode="before")
    @classmethod
    def split_comma_string(cls, v):
        """Transforms comma separated string to list"""
        if isinstance(v, str):
            # Split on commas, strip whitespace, and remove empty entries
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

class PostInSchema(BaseModel):
    """Schema for creating post"""
    title_eng: str
    title_slv: str
    content_eng: str
    content_slv: str
    tags_list: List[str]

    @field_validator("tags_list", mode="before")
    @classmethod
    def split_comma_string(cls, v):
        """Transforms comma separated string to list"""
        if isinstance(v, str):
            # Split on commas, strip whitespace, and remove empty entries
            return [s.strip() for s in v.split(",") if s.strip()]
        return v


class PostOutSchema(BaseModel):
    """Posts query out schema"""
    id: int
    title_eng: str
    title_slv: str
    slug: str
    content_eng: str
    content_slv: str
    active: bool
    tags: List[str]
    author_id: int

    @classmethod
    def from_model(cls, post: "Post"):
        """Create schema from post model"""
        return cls(
            id=post.id,
            title_eng=post.title_eng,
            title_slv=post.title_slv,
            slug=post.slug,
            content_eng=post.content_eng,
            content_slv=post.content_slv,
            active=post.active,
            tags=post.tags,
            author_id=post.author_id
        )

class PostResponseSchema(BaseResponse):
    """Response schema for posts"""
    data: PostOutSchema

class PostsQueryDataSchema(QueryResponseSchema):
    """Posts API base query response"""
    items: list[PostOutSchema]

class PostsQueryResponseSchema(BaseResponse):
    """Posts API query response"""
    data: PostsQueryDataSchema
