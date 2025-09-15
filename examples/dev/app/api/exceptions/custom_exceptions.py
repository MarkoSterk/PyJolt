"""Custom api exceptions"""
from pyjolt.exceptions import BaseHttpException
from pyjolt import HttpStatus

class EntityNotFound(BaseHttpException):
    """Exception for entity not found"""

    def __init__(self, message: str, status_code: HttpStatus = HttpStatus.NOT_FOUND):
        super().__init__(message=message, status_code=status_code)
