"""
Test app implementation
"""
from app.configs import Config
from pyjolt import PyJolt

def create_app(configs = Config) -> PyJolt:
    """App factory"""
    app: PyJolt = PyJolt(__name__, "Test API")
    app.configure_app(configs)

    from app.extensions import db, migrate, auth, scheduler, cache, ai_interface
    db.init_app(app)
    migrate.init_app(app, db)
    auth.init_app(app)
    scheduler.init_app(app)
    cache.init_app(app)
    ai_interface.init_app(app)

    from app.api.models import User, ChatSession

    from app.api.users_api.users_api import UsersApi
    app.register_controller(UsersApi)
    from app.api.auth_api import AuthApi
    app.register_controller(AuthApi)

    from app.api.exceptions.exception_handler import CustomExceptionHandler
    app.register_exception_handler(CustomExceptionHandler)

    return app
