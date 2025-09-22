"""
App configurations
"""
import os

class Config:
    """Config class"""
    SECRET_KEY: str = "46373hdnsfshf73462twvdngnghjdgsfd"
    BASE_PATH: str = os.path.dirname(__file__)
    DEBUG: bool = True

    DATABASE_URI: str = "sqlite+aiosqlite:///./test.db"
    ALEMBIC_DATABASE_URI_SYNC: str = "sqlite:///./test.db"
