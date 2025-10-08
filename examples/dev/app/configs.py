"""
App configurations
"""
import os
from typing import cast
from pyjolt import BaseConfig

class Config(BaseConfig):
    """Config class"""
    APP_NAME: str = cast(str, os.environ.get("APP_NAME"))
    VERSION: str = cast(str, os.environ.get("VERSION"))
    SECRET_KEY: str = cast(str, os.environ.get("SECRET_KEY"))
    BASE_PATH: str = os.path.dirname(__file__)
    DEBUG: bool = BaseConfig.value_to_bool(os.environ.get("DEBUG", "True"))

    DATABASE_URI: str = cast(str, os.environ.get("DATABASE_URI"))
    ALEMBIC_DATABASE_URI_SYNC: str = cast(str, os.environ.get("ALEMBIC_DATABASE_URI_SYNC"))

    CONTROLLERS: list[str] = [
        'app.api.auth_api:AuthApi',
        'app.api.users_api.users_api:UsersApi',
        'app.page.page_controller:PageController'
    ]

    CLI_CONTROLLERS: list[str] = [
        'app.cli.cli_controller:UtilityCLIController'
    ]

    EXTENSIONS: list[str] = [
        'app.extensions:db',
        'app.extensions:migrate',
        'app.authentication:auth',
        'app.ai_interface:ai_interface'
    ]

    MODELS: list[str] = [
        'app.api.models:User',
        'app.api.models:Role'
    ]

    EXCEPTION_HANDLERS: list[str] = [
        'app.api.exceptions.exception_handler:CustomExceptionHandler'
    ]
