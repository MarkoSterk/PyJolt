"""Publication API"""
from time import time_ns
from typing import Any

from app.api.models.publication import Publication
from app.api.schemas.base_schema import ErrorResponseSchema
from app.api.schemas.publication_schemas import (
    PublicationOutSchema,
    PublicationResponseSchema,
    PublicationsQueryResponseSchema,
    PublicationsQuerySchema,
)
from app.extensions import db

from pyjolt import HttpStatus, MediaType, Request, Response, abort
from pyjolt.controller import Controller, Descriptor, get, open_api_docs, path, produces
from pyjolt.database.sql import AsyncSession


@path("/api/v1/publications")
class PublicationsApi(Controller):
    """Publications API controller"""

    @get("/")
    @produces(MediaType.APPLICATION_JSON)
    @db.managed_session
    async def get_publications(self, req: Request,
                session: AsyncSession) -> Response[PublicationsQueryResponseSchema]:
        """Gets all publications"""
        start_time: int = time_ns()
        query_data: PublicationsQuerySchema = PublicationsQuerySchema.model_validate(
                                                                        req.query_params)
        results: dict[str, Any] = await Publication.query_publications(session,
                                                                       query_data)
        end_time: int = time_ns()
        dur: float = (end_time - start_time)/1000000000.0
        self.app.logger.info(f"PERFORMANCE: {dur} s")
        return req.res.json({
            "message": "Query successful",
            "status": "success",
            "data": results
        }).status(HttpStatus.OK)

    @get("/<int:pub_id>")
    @open_api_docs(Descriptor(status=HttpStatus.NOT_FOUND,
                              description="Publication not found.",
                              body=ErrorResponseSchema))
    @produces(MediaType.APPLICATION_JSON)
    @db.managed_session
    async def get_publication_by_id(self, req: Request,
                                    pub_id: int,
                                    session: AsyncSession) -> Response[PublicationResponseSchema]:
        """Gets publication by id"""
        publication: Publication = await Publication.query(session).filter_by(id=pub_id).first()
        if publication is None:
            abort(f"Publication with id {pub_id} not found.", status_code=HttpStatus.NOT_FOUND)
        return req.res.json({
            "message": "Query successful",
            "status": "success",
            "data": PublicationOutSchema.from_model(publication)
        }).status(HttpStatus.OK)

    @get("/<path:doi>")
    @open_api_docs(Descriptor(status=HttpStatus.NOT_FOUND,
                              description="Publication not found.",
                              body=ErrorResponseSchema))
    @produces(MediaType.APPLICATION_JSON)
    @db.managed_session
    async def get_publication_by_doi(self, req: Request,
                                     doi: str,
                                     session: AsyncSession) -> Response[PublicationResponseSchema]:
        """Gets publication by DOI"""
        publication: Publication = await Publication.query(session).filter_by(doi=doi).first()
        if publication is None:
            abort(f"Publication with DOI {doi} not found.", status_code=HttpStatus.NOT_FOUND)
        return req.res.json({
            "message": "Query successful",
            "status": "success",
            "data": PublicationOutSchema.from_model(publication)
        }).status(HttpStatus.OK)
