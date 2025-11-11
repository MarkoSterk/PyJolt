"""
Posts api
"""
from typing import Any, Optional, cast
from pyjolt import MediaType, Response, Request, HttpStatus, abort
from pyjolt.controller import (Controller, path, get, post, put, produces,
                               delete, open_api_docs, Descriptor,
                               consumes)
from pyjolt.database.sql import AsyncSession
from pyjolt.auth import login_required

from app.extensions import db
from app.api.models.post import Post
from app.api.schemas.base_schema import ErrorResponseSchema
from app.api.schemas.post_schemas import (PostsQuery,
                                          PostOutSchema,
                                          PostInSchema,
                                          PostUpdateInSchema,
                                          PostResponseSchema,
                                          PostsQueryResponseSchema)

@path("/api/v1/posts")
class PostsApi(Controller):
    """Posts controller"""

    @get("/")
    @db.managed_session
    @produces(MediaType.APPLICATION_JSON)
    async def get_posts(self, req: Request,
                session: AsyncSession) -> Response[PostsQueryResponseSchema]:
        """Returns all posts"""
        query: PostsQuery = PostsQuery.model_validate(
                                            req.query_params)
        results: dict[str, Any] = await Post.query_posts(session, query)
        return req.res.json({
            "message": "Query successful.",
            "status": "success",
            "data": results
        }).status(HttpStatus.OK)

    @get("/<int:post_id>")
    @produces(MediaType.APPLICATION_JSON)
    @open_api_docs(Descriptor(status=HttpStatus.NOT_FOUND,
                              description="Post not found",
                              body=ErrorResponseSchema))
    @db.managed_session
    async def get_post(self, req: Request, post_id: int,
                       session: AsyncSession) -> Response[PostResponseSchema]:
        """Gets post by id"""
        post_data: Optional[Post] = await Post.query(
            session).filter_by(id=post_id).first()
        if post_data is None:
            abort(f"Post with id {post_id} not found.",
                  status_code=HttpStatus.NOT_FOUND)

        return req.res.json({
            "message": "Post fetched successful",
            "status": "success",
            "data": PostOutSchema.from_model(cast(Post,post_data))
        }).status(HttpStatus.OK)

    @post("/")
    @produces(MediaType.APPLICATION_JSON, status_code=HttpStatus.CREATED)
    @consumes(MediaType.APPLICATION_JSON)
    @open_api_docs(Descriptor(status=HttpStatus.UNAUTHORIZED,
                              description="Not authorized",
                              body=ErrorResponseSchema))
    @db.managed_session
    @login_required
    async def create_post(self, req: Request,
                          post_data: PostInSchema,
                          session: AsyncSession) -> Response[PostResponseSchema]:
        """Creates a new post"""
        new_post: Post = Post(**post_data.model_dump())
        session.add(new_post)
        await session.flush() #to get the ID of the post
        return req.res.json({
            "message": "Post created successfully.",
            "status": "success",
            "data": PostOutSchema.from_model(new_post)
        }).status(HttpStatus.CREATED)

    @delete("/<int:post_id>")
    @produces(MediaType.NO_CONTENT, status_code=HttpStatus.NO_CONTENT)
    @open_api_docs(Descriptor(status=HttpStatus.NOT_FOUND, description="Post not found",
                              body=ErrorResponseSchema),
                Descriptor(status=HttpStatus.UNAUTHORIZED, description="Not authorized",
                              body=ErrorResponseSchema))
    @db.managed_session
    @login_required
    async def delete_post(self, req: Request, post_id: int,
                          session: AsyncSession) -> Response:
        """Deletes post by id"""
        post_data: Post = await Post.query(session).filter_by(id=post_id).first()
        if post_id is None:
            abort(f"Post with id {post_id} not found",
                  status_code=HttpStatus.NOT_FOUND)

        await session.delete(post_data)
        return req.res.no_content()

    @put("/<int:post_id>")
    @consumes(MediaType.APPLICATION_JSON)
    @produces(MediaType.APPLICATION_JSON)
    @open_api_docs(Descriptor(status=HttpStatus.NOT_FOUND, description="Post not found",
                              body=ErrorResponseSchema),
                   Descriptor(status=HttpStatus.UNAUTHORIZED,
                              description="You are not authorized for this action.",
                              body=ErrorResponseSchema))
    @db.managed_session
    @login_required
    async def update_post(self, req: Request, post_id: int,
                          session: AsyncSession,
                          post_data: PostUpdateInSchema) -> Response[PostResponseSchema]:
        """Updates post with post_id"""
        org_post: Post = await Post.query(session).filter_by(id=post_id).first()
        if org_post is None:
            abort(f"Post with id {post_id} not found.", status_code=HttpStatus.NOT_FOUND)

        if org_post.author_id != req.user.id:
            abort("You are not authorized for this action.", status_code=HttpStatus.UNAUTHORIZED)

        for key, value in post_data.model_dump().items():
            if value is not None:
                setattr(org_post, key, value)
        session.add(org_post)

        return req.res.json({
            "message": "Post updated successfully",
            "status": "success",
            "data": PostOutSchema.from_model(org_post)
        }).status(HttpStatus.OK)
