"""Post model for blog posts"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey, Text, event
from pyjolt import Request
from pyjolt.database.sql import AsyncSession
from pyjolt.admin import register_model
from pyjolt.admin.input_fields import TagsInput
from pyjolt.utilities import to_kebab_case
from .base_model import DatabaseModel
from app.api.schemas.post_schemas import (PostsQuery, PostInSchema,
                                          any_tag_in_csv_condition,
                                          PostOutSchema)

if TYPE_CHECKING:
    from .user import User

@register_model
class Post(DatabaseModel):
    """Post model"""
    __tablename__ = "posts"

    class Meta:
        exclude_from_create_form = ["created_at", "slug"]
        exclude_from_update_form = ["created_at", "slug"]
        exclude_from_table = ["slug", "content_slv"]
        order_table_by = ["created_at DESC"]
        custom_labels = {
            "title_eng": "Title (EN)",
            "title_slv": "Title (SLV)",
            "content_eng": "Content (EN)",
            "content_slv": "Content (SLV)",
            "id": "ID"
        }
        form_fields_order = ["title_slv", "title_eng", "content_slv", "content_eng", "active", "tags_list"]
        custom_form_fields = [
            TagsInput(id="tags_list", name="tags_list", label="Tags", as_string=True)
        ]
        create_validation_shema = PostInSchema
        update_validation_shema = PostInSchema

    title_eng: Mapped[str] = mapped_column()
    title_slv: Mapped[str] = mapped_column()
    slug: Mapped[str] = mapped_column(unique=True)
    content_eng: Mapped[str] = mapped_column(Text, nullable=False)
    content_slv: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(default=True)
    tags_list: Mapped[str] = mapped_column(nullable=False, default="")

    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    author: Mapped[User] = relationship(back_populates="posts")

    @property
    def tags(self) -> list[str]:
        """Tags of the post"""
        return [t for t in (self.tags_list.split(",") if self.tags_list else []) if t]

    @tags.setter
    def tags(self, value: list[str]):
        norm = [t.strip().lower() for t in value if t and t.strip()]
        self.tags_list = ",".join(norm)

    @classmethod
    async def query_posts(cls, session: AsyncSession,
                          query_data: PostsQuery) -> dict[str, Any]:
        """Performs query for posts"""
        conds = []
        if query_data.active is not None:
            conds.append(cls.active == query_data.active)
        if query_data.created_at is not None:
            conds.append(cls.created_at >= query_data.created_at)
        if query_data.tags:
            conds.append(any_tag_in_csv_condition(query_data.tags, Post))
        if query_data.user_id is not None:
            conds.append(cls.author_id == query_data.user_id)

        results: dict[str, Any] = await Post.query(session).filter(
            *conds
        ).paginate(page=query_data.page, per_page=query_data.per_page)
        results["items"] = [PostOutSchema.from_model(post)
                          for post in results["items"]]
        return results
    
    async def admin_create(self, req: "Request", new_data: dict[str, Any],
                           session: "AsyncSession"):
        """Saves the post from admin interface. Sets author_id from request user."""
        new_data["tags_list"] = ",".join(new_data["tags_list"])
        for key, value in new_data.items():
            setattr(self, key, value)
        self.author_id = req.user.id
        session.add(self)
    
    #this hook or "before_update" can be used for modifying the tags_list from list[str] to str
    async def admin_update(self, req: "Request", new_data: dict[str, Any],
                           session: "AsyncSession"):
        tags: Optional[str] = None
        if new_data.get("tags_list"):
            tags = ",".join(new_data["tags_list"])
            new_data["tags_list"] = tags
        for key, value in new_data.items():
            setattr(self, key, value)
        session.add(self)

@event.listens_for(Post, "before_insert")
def set_slug_before_insert(mapper, connection, target: Post):
    if target.title_eng:
        target.slug = to_kebab_case(target.title_eng)


@event.listens_for(Post, "before_update")
def set_slug_before_update(mapper, connection, target: Post):
    # Only update if title_eng changed or slug is empty
    if target.title_eng and (not target.slug or target.slug != to_kebab_case(target.title_eng)):
        target.slug = to_kebab_case(target.title_eng)
    # if target.tags_list:
    #     target.tags_list = ",".join(target.tags_list)
