"""Development utilities"""
import re
from typing import Any
import requests
from requests import Response
from pyjolt.database.sql import AsyncSession
from pyjolt.cli import CLIController, command, argument
from faker import Faker

from app.api.models.post import Post
from app.api.models.publication import Publication
from app.extensions import db

from .publications_doi import dois

def slugify(s: str) -> str:
    """
    Slugyfies text
    """
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)      # drop non-word chars
    s = re.sub(r"[\s_-]+", "-", s)      # collapse to single hyphens
    s = s.strip("-")
    return s or "post"

class DevUtilities(CLIController):
    """Simple dev utility controller"""

    @command("create-posts")
    @argument("number", int)
    @db.managed_session_for_cli
    async def create_fake_posts(self, number: int, session: AsyncSession):
        """Creates any number of fake posts"""
        fake: Faker = Faker()
        posts: list[Post] = []
        for _ in range(number):
            title_en = fake.sentence().rstrip(".")
            title_sl = fake.sentence().rstrip(".")
            content_en = "\n\n".join(fake.paragraphs(nb=5))
            content_sl = "\n\n".join(fake.paragraphs(nb=5))
            candidate_slug = slugify(title_en)

            post = Post(
                title_eng=title_en,
                title_slv=title_sl,
                slug=candidate_slug,
                content_eng=content_en,
                content_slv=content_sl,
                active=True,
                tags_list=",".join([t.lower() for t in fake.words(nb=5)]),
                author_id=1
            )
            posts.append(post)
        session.add_all(posts)
        print(f"Created {number} of posts")

    @command("fetch-publications")
    @db.managed_session_for_cli
    async def fetch_publications(self, session: AsyncSession):
        """
        Fetched all publications data from DOI list
        Uses api.crossref.com
        """
        base_url: str = self.app.get_conf("CROSSREF_API_URL")
        pubs: list[Publication] = []
        for doi in dois:
            try:
                response: Response = requests.get(f"{base_url}/{doi}", timeout=20)
                if response.status_code != 200:
                    print(f"Failed to fetch (status={response.status_code}): ", doi)
                    continue
                data: dict[str, Any] = response.json()
                publication = Publication.from_crossref_api(data)
                pubs.append(publication)
                #print("Fetched: ", doi)
            #pylint: disable-next=W0718
            except Exception as e:
                print(f"Exception for {doi}: ", e)
        session.add_all(pubs)

        print(f"Fetched {len(pubs)}/{len(dois)}")
