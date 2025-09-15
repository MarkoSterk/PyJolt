"""
Test app implementation
"""
from app.configs import Config
from pyjolt import PyJolt


def create_app(configs = Config) -> PyJolt:
    """App factory"""
    app: PyJolt = PyJolt(__name__, "PyJolt Test")
    app.configure_app(configs)

    from app.api.users_api.users_api import UsersApi
    app.register_controller(UsersApi)

    from app.api.exceptions.exception_handler import CustomExceptionHandler
    app.register_exception_handler(CustomExceptionHandler)

    return app
