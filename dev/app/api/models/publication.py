"""Publication data model"""
from datetime import datetime
from typing import Any, Self, cast, TYPE_CHECKING
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Text, DateTime
from pyjolt.database.sql import AsyncSession
from pyjolt.admin import register_model

from app.api.schemas.publication_schemas import PublicationOutSchema

from .base_model import DatabaseModel

if TYPE_CHECKING:
    from ..schemas.publication_schemas import PublicationsQuerySchema

@register_model
class Publication(DatabaseModel):
    """Post model"""
    __tablename__ = "publications"
    __exclude_in_form__ = ["created_at"]
    __exclude_in_table__ = ["funders_list", "abstract", "volume", "page", "created_at", "pub_type"]
    __labels__ = {
        "doi": "DOI",
        "authors": "Authors List",
        "container_title": "Journal Name",
        "publisher": "Publisher",
        "id": "ID",
        "title": "Title",
    }

    doi: Mapped[str] = mapped_column(nullable=False, unique=True)
    authors_list: Mapped[str] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    pub_type: Mapped[str] = mapped_column(nullable=False, default="journal-article")
    publisher: Mapped[str] = mapped_column(nullable=True)
    container_title: Mapped[str] = mapped_column(nullable=False)
    page: Mapped[str] = mapped_column(nullable=True)
    volume: Mapped[str] = mapped_column(nullable=True)
    date_published: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    funders_list: Mapped[str] = mapped_column(nullable=True)
    abstract: Mapped[str] = mapped_column(Text, nullable=True)

    @property
    def authors(self) -> list[str]:
        """Authors as a list"""
        return self.authors_list.split(",")

    @authors.setter
    def authors(self, authors: list[str]):
        """Sets authors as a string"""
        self.authors_list = ",".join(authors)

    @property
    def funders(self) -> list[str]|None:
        """List of funders"""
        if self.funders_list is None:
            return None
        return self.funders_list.split(",")

    @funders.setter
    def funders(self, funders: list[str]):
        """Sets list of funders"""
        self.funders_list = ",".join(funders)

    @classmethod
    def from_crossref_api(cls, crossref_response: dict[str, Any]) -> Self:
        """Creates new publication instance from CrossrefApi data"""
        data: dict[str, Any] = cast(dict[str, Any], crossref_response.get("message"))
        authors: str = ",".join([f'{author["given"]} {author["family"]}'
                                 for author in data["author"]])
        #all_funders: Optional[list[dict[str, Any]]|str] = data.get("funder", None)
        #print(f'Authors for {data["DOI"]}: ', authors)
        return cls(
            doi=data["DOI"],
            authors_list=authors,
            title=data["title"][0],
            pub_type=data["type"],
            publisher=data["publisher"],
            container_title=data.get("container-title",[None])[0],
            page=data.get("page"),
            volume=data.get("volume"),
            date_published=datetime.fromisoformat(data["created"]["date-time"]),
            abstract=data.get("abstract")
        )

    @classmethod
    async def query_publications(cls, session: AsyncSession,
                           query_data: "PublicationsQuerySchema") -> dict[str, Any]:
        """Performs query"""
        conds = []
        if query_data.title is not None:
            conds.append(query_data.title in cls.title)
        if query_data.date_published is not None:
            conds.append(cls.date_published >= query_data.date_published)
        if query_data.publisher:
            conds.append(query_data.publisher in cls.publisher)
        if query_data.container_title is not None:
            conds.append(query_data.container_title in cls.container_title)
        if query_data.pub_type is not None:
            conds.append(cls.pub_type == query_data.pub_type)

        publications: dict[str, Any] = await cls.query(session).filter(
            *conds
        ).paginate(page=query_data.page, per_page=query_data.per_page)
        publications["items"] = [PublicationOutSchema.from_model(post)
                          for post in publications["items"]]
        return publications
