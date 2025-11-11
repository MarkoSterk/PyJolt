"""Main exception handler"""
from pyjolt import MediaType, Request, Response, HttpStatus
from pyjolt.controller import produces
from pyjolt.exceptions import (ExceptionHandler,
                               handles,
                               AuthenticationException,
                               AborterException)
from pyjolt.admin import AdminEnterError
from pydantic import ValidationError

class CustomExceptionHandler(ExceptionHandler):
    """Exception handler implementation"""

    @handles(AuthenticationException)
    async def unauthorized(self, req: Request, _: AuthenticationException) -> Response:
        """Handles authentication exceptions"""
        return req.res.json({
            "message": "Login required",
            "status": "error"
        }).status(HttpStatus.FORBIDDEN)

    @handles(AborterException)
    async def aborter_exception(self, req: Request, exc: AborterException) -> Response:
        """Handles aborter exceptions"""
        return req.res.json({
            "message": exc.message,
            "status": exc.status
        }).status(exc.status_code)

    @handles(ValidationError)
    async def validation_error(self, req: Request, exc: ValidationError) -> Response:
        """Handles validation errors"""
        details = {}
        if hasattr(exc, "errors"):
            for error in exc.errors():
                details[error["loc"][0]] = error["msg"]

        return req.response.json({
            "message": "Validation failed.",
            "details": details
        }).status(HttpStatus.UNPROCESSABLE_ENTITY)

    @handles(AdminEnterError)
    @produces(MediaType.TEXT_HTML)
    async def admin_enter_error(self, req: Request, exc: AdminEnterError) -> Response:
        """Handles admin dashboard enter error"""
        print("IN ERROR HANDLER: ", exc.message)
        return (await req.res.html_from_string(
            "<h1>You don't have permission to enter the dashboard</h1>"
        )).status(HttpStatus.OK)
