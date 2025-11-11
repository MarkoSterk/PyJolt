"""Projects API"""
from typing import Any
from pyjolt import Request, Response, HttpStatus, MediaType, abort
from pyjolt.controller import (Controller, path,
                               get, produces, open_api_docs,
                               Descriptor)
from pyjolt.database.sql import AsyncSession

from app.extensions import db
from app.api.models.project import Project
from app.api.schemas.base_schema import ErrorResponseSchema
from app.api.schemas.project_schemas import (ProjectOutSchema,
                                             ProjectQuerySchema,
                                             ProjectsQueryResponseSchema,
                                             ProjectResponseSchema)

@path("/api/v1/projects")
class ProjectsApi(Controller):
    """Projects api controller"""

    @get("/")
    @produces(MediaType.APPLICATION_JSON)
    @db.managed_session
    async def get_projects(self, req: Request,
                    session: AsyncSession) -> Response[ProjectsQueryResponseSchema]:
        """Fetches all projects"""
        query_data: ProjectQuerySchema = ProjectQuerySchema.model_validate(req.query_params)
        result: dict[str, Any] = await Project.query_projects(session, query_data)

        return req.res.json({
            "message": "Query successful",
            "status": "success",
            "data": result
        }).status(HttpStatus.OK)

    @get("/<int:project_id>")
    @produces(MediaType.APPLICATION_JSON)
    @open_api_docs(Descriptor(status=HttpStatus.NOT_FOUND,
                              description="Project not found",
                              body=ErrorResponseSchema))
    @db.managed_session
    async def get_project_by_id(self, req: Request,
                          project_id: int,
                          session: AsyncSession) -> Response[ProjectResponseSchema]:
        """Fetches project by id"""
        project: Project = await Project.query(session).filter_by(id=project_id).first()
        if project is None:
            abort(f"Project with id {project_id} not found.",
                  status_code=HttpStatus.NOT_FOUND)

        return req.res.json({
            "message": "Project fetched successfully",
            "status": "success",
            "data": ProjectOutSchema.from_model(project).model_dump()
        }).status(HttpStatus.OK)

    @get("/<string:project_code>")
    @produces(MediaType.APPLICATION_JSON)
    @open_api_docs(Descriptor(status=HttpStatus.NOT_FOUND,
                              description="Project not found",
                              body=ErrorResponseSchema))
    @db.managed_session
    async def get_project_by_code(self, req: Request,
                                  project_code: str,
                                  session: AsyncSession) -> Response[ProjectResponseSchema]:
        """Fetches project by project code"""
        project: Project = await Project.query(session).filter_by(code=project_code).first()
        if project is None:
            abort(f"Project with code {project_code} does not exist",
                  status_code=HttpStatus.NOT_FOUND)

        return req.res.json({
            "message": "Project fetched successfully",
            "status": "success",
            "data": ProjectOutSchema.from_model(project).model_dump()
        }).status(HttpStatus.OK)
