"""
App configurations
"""
import os
from typing import Type, cast, Any #,Type
from pyjolt import BaseConfig
#from pyjolt.caching.backends.memory_cache_backend import MemoryCacheBackend
from pyjolt.caching.backends.sqlite_cache_backend import SQLiteCacheBackend
from pyjolt.database.nosql.backends import MongoBackend

class Config(BaseConfig):
    """Config class"""
    APP_NAME: str = cast(str, os.environ.get("APP_NAME"))
    VERSION: str = cast(str, os.environ.get("VERSION"))
    SECRET_KEY: str = cast(str, os.environ.get("SECRET_KEY"))
    BASE_PATH: str = os.path.dirname(__file__)
    DEBUG: bool = BaseConfig.value_to_bool(os.environ.get("DEBUG", "True"))

    NOSQL_DATABASE: dict[str, str] = {
        #"NOSQL_BACKEND": MongoBackend,
        "NOSQL_DATABASE_URI": cast(str, os.environ.get("NOSQL_DATABASE_URI")),
        "NOSQL_DATABASE_NAME": cast(str, os.environ.get("NOSQL_DATABASE_NAME")),
        "NOSQL_DB_INJECT_NAME": cast(str, os.environ.get("NOSQL_DB_INJECT_NAME", None)),
        "NOSQL_SESSION_NAME": cast(str, os.environ.get("NOSQL_SESSION_NAME", None)),
    }

    SQL_DATABASE: dict[str, str] = {
        "DATABASE_URI": cast(str, os.environ.get("DATABASE_URI")),
        "ALEMBIC_DATABASE_URI_SYNC": cast(str, os.environ.get("ALEMBIC_DATABASE_URI_SYNC"))
    }

    CACHE_BACKEND: Type[SQLiteCacheBackend] = SQLiteCacheBackend #default is MemoryCacheBackend
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
        # 'app.extensions:cache',
        # 'app.authentication:auth',
        # 'app.ai_interface:ai_interface'
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

    LOGGERS: list[str] = [
        'app.logging.file_logger:FileLogger'
    ]

    FILE_LOGGER: dict[str, Any] = {
        "SINK": os.path.join(BASE_PATH, "logs", "file.jsonl"),
        "LEVEL": "TRACE",
        "ENQUEUE": True,
        "DELAY": True
    }
