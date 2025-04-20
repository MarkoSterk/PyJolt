"""
Collection of http exceptions that can be raised
"""
from pydantic import ValidationError as PydanticValidationError


class BaseHttpException(Exception):
    """
    Base http exception class
    """
    def __init__(self, message = "",
                 status_code = 500,
                 status = "error",
                 data = None):
        """
        Init method
        """
        self.message = message
        self.status_code = status_code
        self.status = status
        self.data = data

class StaticAssetNotFound(BaseHttpException):
    """
    HTTP exception for static assets not found
    """
    def __init__(self, message: str = "Static asset not found",
                 status_code: int = 404,
                 status: str = "error",
                 data: any = None):
        super().__init__(
            message,
            status_code,
            status,
            data
        )


class AborterException(BaseHttpException):
    """
    Aborter exception
    """
    def __init__(self, message: str = "",
                 status_code: int = 400,
                 status: str = "error",
                 data: any = None):
        super().__init__(
            message,
            status_code,
            status,
            data
        )

class MissingRequestData(BaseHttpException):
    """
    Exception for missing request data. 
    Raised by input decorator on route handlers
    """
    def __init__(self, message: str = "",
                 status_code: int = 400,
                 status: str = "error",
                 data: any = None):
        super().__init__(
            message,
            status_code,
            status,
            data
        )

class SchemaValidationError(BaseHttpException, PydanticValidationError):
    """
    Exception for schema validation errors
    """
    def __init__(self, message: list[str]|list|dict):
        super().__init__(
            "Data validation failed",
            422,
            "error",
            message
        )

class PydanticSchemaValidationError(BaseHttpException):
    """
    Exception for schema validation errors with Pydantic
    """
    def __init__(self, messages: list[dict]):
        parsed_messages = {}
        for obj in messages:
            loc: str = obj["loc"][0]
            if loc not in parsed_messages:
                parsed_messages[loc] = []
            parsed_messages[loc].append(obj["msg"])
        super().__init__("Data validation failed",
                         422,
                         "error",
                         parsed_messages)

class AuthenticationException(BaseHttpException):
    """
    Authentication exception for endpoints which require authentication
    """
    def __init__(self, message: str):
        super().__init__(
            message,
            401,
            "error",
            None
        )

class InvalidJWTError(BaseHttpException):
    """
    Invalid or expired JWT token error
    """
    def __init__(self, message: str):
        super().__init__(
            message,
            401,
            "error",
            None
        )

def abort(msg: str, status_code: int, status: str = "", data: any = None):
    """
    Aborts request by raising an aborter exception
    """
    raise AborterException(msg, status_code, status, data)
