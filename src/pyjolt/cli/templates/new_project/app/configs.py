"""
App configurations
"""
import os

class Config:
    """Config class"""
    BASE_PATH: str = os.path.dirname(__file__)
    DEBUG: bool = True #for development and live reloading
    HOST: str = "localhost"
    PORT: int = 8080
    LIFESPAN: str = "on" #for server events - on_startup, on_shutdown etc. Needed by the database extension for initial db conection

    SECRET_KEY: str = "2354gtzfregeqr73473asgDAH3242" #replace this with a secure key

    ##For database connections
    ##string for database connection string. Must include an async compatible driver
    DATABASE_URI: str = "sqlite+aiosqlite:///test.db"
    ##sync db connection for database migrations
    ALEMBIC_DATABASE_URI_SYNC: str = "sqlite:///test.db"
