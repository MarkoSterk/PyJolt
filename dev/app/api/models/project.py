"""Project model"""
from typing import Any
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column
from pyjolt.database.sql import AsyncSession
from pyjolt.admin import register_model

from app.api.schemas.project_schemas import ProjectQuerySchema, ProjectOutSchema
from .base_model import DatabaseModel

@register_model
class Project(DatabaseModel):
    """Project db model"""

    __tablename__ = "projects"

    title_slv: Mapped[str] = mapped_column(Text, nullable=False)
    title_eng: Mapped[str] = mapped_column(Text, nullable=True)
    leader: Mapped[str] = mapped_column(Text, nullable=False)
    duration: Mapped[str] = mapped_column(Text, nullable=False)
    sicris_url: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    abstract_slv: Mapped[str] = mapped_column(Text, nullable=True)
    abstract_eng: Mapped[str] = mapped_column(Text, nullable=True)
    keywords_slv: Mapped[str] = mapped_column(Text, nullable=False)
    keywords_eng: Mapped[str] = mapped_column(Text, nullable=True)
    researchers: Mapped[str] = mapped_column(Text, nullable=False)

    @classmethod
    async def query_projects(cls, session: AsyncSession,
                             query_data: "ProjectQuerySchema") -> dict[str, Any]:
        """Queries projects"""
        conds = []
        if query_data.title_slv is not None:
            conds.append(query_data.title_slv in cls.title_slv)
        if query_data.title_eng is not None:
            conds.append(query_data.title_eng in cls.title_eng)
        if query_data.end_date is not None:
            conds.append(query_data.end_date.strftime("%YYYY-%MM-%dd") in cls.duration)
        if query_data.start_date is not None:
            conds.append(query_data.start_date.strftime("%YYYY-%MM-%dd") in cls.duration)
        if query_data.keywords_slv is not None:
            conds.append(query_data.keywords_slv in cls.keywords_slv)
        if query_data.keywords_eng is not None:
            conds.append(query_data.keywords_eng in cls.keywords_eng)
        if query_data.leader is not None:
            conds.append(query_data.leader in cls.leader)
        if query_data.researchers is not None:
            rsrs: list[str] = query_data.researchers.split(",")
            for rsr in rsrs:
                conds.append(rsr.strip() in cls.researchers)
        projects: dict[str, Any] = await cls.query(session).filter(
            *conds
        ).paginate(page=query_data.page, per_page=query_data.per_page)
        projects["items"] = [ProjectOutSchema.from_model(project)
                          for project in projects["items"]]
        return projects
