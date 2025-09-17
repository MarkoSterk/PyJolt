"""
Test app implementation
"""
from app.configs import Config
from pyjolt import PyJolt


def create_app(configs = Config) -> PyJolt:
    """App factory"""
    app: PyJolt = PyJolt(__name__, "Test API")
    app.configure_app(configs)

    from app.extensions import db, migrate
    db.init_app(app)
    migrate.init_app(app, db)

    from app.api.models import User

    from app.api.users_api.users_api import UsersApi
    app.register_controller(UsersApi)

    from app.api.exceptions.exception_handler import CustomExceptionHandler
    app.register_exception_handler(CustomExceptionHandler)

    return app
