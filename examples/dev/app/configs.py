"""
App configurations
"""
import os
from pyjolt import BaseConfig

class Config(BaseConfig):
    """Config class"""
    APP_NAME: str = "Test app"
    VERSION: str = "1.0"
    SECRET_KEY: str = "46373hdnsfshf73462twvdngnghjdgsfd"
    BASE_PATH: str = os.path.dirname(__file__)
    DEBUG: bool = True

    DATABASE_URI: str = "sqlite+aiosqlite:///./test.db"
    ALEMBIC_DATABASE_URI_SYNC: str = "sqlite:///./test.db"

    CONTROLLERS: list[str] = [
        'app.api.auth_api:AuthApi',
        'app.api.chat_api.chat_api:ChatApi',
        'app.api.users_api.users_api:UsersApi'
    ]

    EXTENSIONS: list[str] = [
        'app.extensions:db',
        'app.extensions:migrate',
        'app.extensions:cache',
        'app.authentication:auth',
        'app.scheduler:scheduler',
        'app.ai_interface:ai_interface'
    ]

    MODELS: list[str] = [
        'app.api.models:User',
        'app.api.models:ChatSession',
        'app.api.models:Role'
    ]

    EXCEPTION_HANDLERS: list[str] = [
        'app.api.exceptions.exception_handler:CustomExceptionHandler'
    ]
