"""Researchers API"""
from pyjolt import HttpStatus, MediaType, Request, Response, abort
from pyjolt.controller import (Controller, path,
                               get, produces,
                               open_api_docs, Descriptor)
from pyjolt.database.sql import AsyncSession

from app.extensions import db
from app.api.models.researcher import Researcher
from app.api.schemas.base_schema import ErrorResponseSchema
from app.api.schemas.researcher_schemas import (ResearcherOutSchema,
                                                AllResearchersResponseSchema,
                                                ResearcherResponseSchema)

@path("/api/v1/researchers")
class ResearchersApi(Controller):
    """Researchers api controller"""

    @get("/")
    @produces(MediaType.APPLICATION_JSON)
    @db.managed_session
    async def get_researchers(self, req: Request,
                        session: AsyncSession) -> Response[AllResearchersResponseSchema]:
        """Fetches all researchers"""
        researchers: list[Researcher] = await Researcher.query(session).all()

        return req.res.json({
            "message": "Researchers fetched successfully",
            "status": "success",
            "data": [ResearcherOutSchema.from_model(rsr)
                        for rsr in researchers]
        }).status(HttpStatus.OK)

    @get("/<int:rsr_id>")
    @produces(MediaType.APPLICATION_JSON)
    @open_api_docs(Descriptor(status=HttpStatus.NOT_FOUND,
                              description="Researcher not found",
                              body=ErrorResponseSchema))
    @db.managed_session
    async def get_researcher_by_id(self, req: Request,
                        rsr_id: int,
                        session: AsyncSession) -> Response[ResearcherResponseSchema]:
        """Fetches researcher by id"""
        researcher: Researcher = await Researcher.query(session).filter_by(id=rsr_id).first()
        if researcher is None:
            abort(f"Researcher with id {rsr_id} does not exist.",
                  status_code=HttpStatus.NOT_FOUND)
        return req.res.json({
            "message": "Researcher fetched successfully",
            "status": "success",
            "data": ResearcherOutSchema.from_model(researcher)
        }).status(HttpStatus.OK)

    @get("/<string:rsr_code>")
    @produces(MediaType.APPLICATION_JSON)
    @open_api_docs(Descriptor(status=HttpStatus.NOT_FOUND,
                              description="Researcher not found",
                              body=ErrorResponseSchema))
    @db.managed_session
    async def get_researcher_by_code(self, req: Request,
                            rsr_code: str,
                            session: AsyncSession) -> Response[ResearcherResponseSchema]:
        """Fetches researcher by rsr code"""
        researcher: Researcher = await Researcher.query(session).filter_by(code=rsr_code).first()
        if researcher is None:
            abort(f"Researcher with code {rsr_code} does not exist.",
                  status_code=HttpStatus.NOT_FOUND)
        return req.res.json({
            "message": "Researcher fetched successfully",
            "status": "success",
            "data": ResearcherOutSchema.from_model(researcher)
        }).status(HttpStatus.OK)
