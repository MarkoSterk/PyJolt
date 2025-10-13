"""
App configurations
"""
import os
from typing import Type, cast #,Type
from pyjolt import BaseConfig
from pyjolt.caching.memory_cache_backend import MemoryCacheBackend
from pyjolt.database.nosql.backends import MongoBackend

class Config(BaseConfig):
    """Config class"""
    APP_NAME: str = cast(str, os.environ.get("APP_NAME"))
    VERSION: str = cast(str, os.environ.get("VERSION"))
    SECRET_KEY: str = cast(str, os.environ.get("SECRET_KEY"))
    BASE_PATH: str = os.path.dirname(__file__)
    DEBUG: bool = BaseConfig.value_to_bool(os.environ.get("DEBUG", "True"))

    NOSQL_BACKEND: Type[MongoBackend] = MongoBackend
    NOSQL_URI: str = cast(str, os.environ.get("NOSQL_URI"))
    NOSQL_DATABASE: str = cast(str, os.environ.get("NOSQL_DATABASE", "testdb"))

    DATABASE_URI: str = cast(str, os.environ.get("DATABASE_URI"))
    ALEMBIC_DATABASE_URI_SYNC: str = cast(str, os.environ.get("ALEMBIC_DATABASE_URI_SYNC"))

    CACHE_BACKEND: Type[MemoryCacheBackend] = MemoryCacheBackend #default is MemoryCacheBackend
    CACHE_DURATION: int = 500 #default is 300 s

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
        'app.extensions:cache',
        'app.extensions:nosqldb',
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

    MIDDLEWARE: list[str] = [
        'app.middleware.timing_mw:TimingMW'
    ]
