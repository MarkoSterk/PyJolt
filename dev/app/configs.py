"""
App configs
"""
import os
from typing import Any, cast

from pyjolt import BaseConfig, LogLevel
from pyjolt.admin import AdminConfigs

class Config(BaseConfig):
    """
    All application configurations
    """

    APP_NAME: str = cast(str, os.environ.get("APP_NAME", None))
    BASE_PATH: str = os.path.dirname(__file__)
    DEBUG: bool = BaseConfig.value_to_bool(os.environ.get("DEBUG", True))
    SECRET_KEY: str = cast(str, os.environ.get("SECRET_KEY", None))
    VERSION: str = cast(str, os.environ.get("VERSION", None))

    COOKIE_NAME: str = cast(str, os.environ.get("COOKIE_NAME", None))
    COOKIE_DURATION: int = int(cast(int, os.environ.get("COOKIE_DURATION", None)))

    CROSSREF_API_URL: str = cast(str, os.environ.get("CROSSREF_API_URL"))
    INSTITUTE_EMAIL: str = cast(str, os.environ.get("INSTITUTE_EMAIL"))

    CORS_ALLOW_ORIGINS: list[str] = [
        "http://localhost:8080",
    ]

    ADMIN_DASHBOARD: AdminConfigs = {
        "URL_FOR_FOR_LOGIN": "AuthApi.login_form",
        "URL_FOR_FOR_LOGOUT": "AuthApi.logout",
    }

    SQL_DATABASE: dict[str, Any] = {
        "DATABASE_URI": cast(str, os.environ.get("DATABASE_URI", None)),
        "ALEMBIC_DATABASE_URI_SYNC": cast(str, os.environ.get("ALEMBIC_DATABASE_URI_SYNC", None)),
        "SHOW_SQL": False,
        "NICE_NAME": "Super cool sqlite db"
    }

    EMAIL_CLIENT: dict[str, str|int|bool] = {
        "SENDER_NAME_OR_ADDRESS": "info@physio-mb.si",
        "SMTP_SERVER": "localhost",
        "SMTP_PORT": 1025,
        "USE_TLS": False
    }

    SECOND_EMAIL: dict[str, str|int|bool] = {
        "SENDER_NAME_OR_ADDRESS": "newsletter@physio-mb.si",
        "SMTP_SERVER": "localhost",
        "SMTP_PORT": 1025,
        "USE_TLS": False
    }

    MODELS: list[str] = [
        "app.api.models.user:User",
        "app.api.models.post:Post",
        "app.api.models.publication:Publication",
        "app.api.models.project:Project",
        "app.api.models.researcher:Researcher"
    ]

    CONTROLLERS: list[str] = [
        "app.api.auth.auth_api:AuthApi",
        "app.api.posts.posts_api:PostsApi",
        "app.api.publications.publications_api:PublicationsApi",
        "app.api.projects.projects_api:ProjectsApi",
        "app.api.researchers.researchers_api:ResearchersApi"
    ]

    CLI_CONTROLLERS: list[str] = [
        "app.cli.user_management:UserManagamentCli",
        "app.cli.dev_utils:DevUtilities"
    ]

    EXCEPTION_HANDLERS: list[str] = [
        "app.api.exception_handlers.exception_handler:CustomExceptionHandler"
    ]

    EXTENSIONS: list[str] = [
        "app.extensions:db",
        "app.extensions:migrate",
        "app.extensions:email",
        "app.extensions:second_email",
        "app.task_manager:scheduler_manager",
        "app.admin:admin_extension",
        "app.extensions:cache"
    ]

    # LOGGERS: list[str] = [
    #     "app.loggers.performance_logger:PerformanceFileLogger"
    # ]

    MIDDLEWARE: list[str] = [
        "app.middleware.timing_mw:TimingMW",
        "app.middleware.auth_mw:AuthMW"
    ]

    PERFORMANCE_FILE_LOGGER: dict[str, Any] = {
        "SINK": os.path.join(BASE_PATH, "logging", "performance_log.log"),
        "LEVEL": LogLevel.INFO,
        "ENQUEUE": True,
        "BACKTRACE": True,
        "DIAGNOSE": True,
        "COLORIZE": False,
        "DELAY": True,
        "ROTATION": "5 MB",
        "RETENTION": 5,
        "COMPRESSION": "zip",
        "SERIALIZE": False,
        "ENCODING": "utf-8",
        "MODE": "a"
    }
