"""
Exception handler api
"""
from typing import Any
from pydantic import BaseModel, ValidationError
from pyjolt.exceptions import ExceptionController, handles
from pyjolt import Request, Response, HttpStatus

from .custom_exceptions import EntityNotFound

class ErrorResponse(BaseModel):
    message: str
    details: Any|None = None

class CustomExceptionController(ExceptionController):

    @handles(EntityNotFound)
    async def not_found(self, req: "Request", exc: EntityNotFound) -> "Response[ErrorResponse]":
        """Handles not found exceptions"""
        return req.response.json({
            "message": exc.message
        }).status(exc.status_code)
    
    @handles(ValidationError)
    async def validation_error(self, req: "Request", exc: ValidationError) -> "Response[ErrorResponse]":
        """Handles validation errors"""
        return req.response.json({
            "message": "Validation failed.",
            "details": exc.errors() if hasattr(exc, "errors") else []
        }).status(HttpStatus.UNPROCESSABLE_ENTITY)
