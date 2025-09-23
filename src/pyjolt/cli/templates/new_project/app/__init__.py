"""
Test app implementation
"""
from pyjolt import PyJolt
from app.configs import Config

def create_app(configs = Config) -> PyJolt:
    """App factory"""
    app: PyJolt = PyJolt(__name__)
    app.configure_app(configs)

    ##First initilize extensions
    from app.extensions import auth, db, migrate
    db.init_app(app)
    migrate.init_app(app, db)
    auth.init_app(app)

    ##Register controllers
    from app.api.example_api import ExampleApi
    app.register_controller(ExampleApi)

    ##Register exception handlers
    from app.api.exceptions import Handler
    app.register_exception_handler(Handler)

    #import database models for correct detection
    #with the migration extension

    return app
