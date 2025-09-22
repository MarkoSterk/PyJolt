"""
Exception handler api
"""
from typing import Any
from pydantic import BaseModel, ValidationError
from pyjolt.exceptions import ExceptionHandler, handles, AuthenticationException, UnauthorizedException
from pyjolt import Request, Response, HttpStatus
from pyjolt.ai_interface import ChatSessionNotFound

from .custom_exceptions import EntityNotFound

class ErrorResponse(BaseModel):
    message: str
    details: Any|None = None

class CustomExceptionHandler(ExceptionHandler):

    @handles(EntityNotFound)
    async def not_found(self, req: "Request", exc: EntityNotFound) -> "Response[ErrorResponse]":
        """Handles not found exceptions"""
        return req.response.json({
            "message": exc.message
        }).status(exc.status_code)
    
    @handles(ValidationError)
    async def validation_error(self, req: "Request", exc: ValidationError) -> "Response[ErrorResponse]":
        """Handles validation errors"""
        details = {}
        if hasattr(exc, "errors"):
            for error in exc.errors():
                details[error["loc"][0]] = error["msg"]

        return req.response.json({
            "message": "Validation failed.",
            "details": details
        }).status(HttpStatus.UNPROCESSABLE_ENTITY)
    
    @handles(AuthenticationException)
    async def auth_exception(self, req: "Request", exc: AuthenticationException) -> "Response[ErrorResponse]":
        """Handles authentication errors"""
        return req.response.json({
            "message": exc.message,
            "details": "error"
        }).status(exc.status_code)
    
    @handles(UnauthorizedException)
    async def unauthorized_exception(self, req: "Request", exc: UnauthorizedException) -> "Response[ErrorResponse]":
        """Handled unauthorized access errors"""
        return req.response.json({
            "message": exc.message,
            "details": exc.data,
        }).status(exc.status_code)
    
    @handles(ChatSessionNotFound)
    async def chat_session_not_found(self, req: "Request", exc: ChatSessionNotFound) -> "Response[ErrorResponse]":
        """Handles chat session not found exception"""
        return req.response.json({
            "message": exc.message
        }).status(exc.status_code)
