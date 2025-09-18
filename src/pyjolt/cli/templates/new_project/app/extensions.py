"""
Import all extensions and initilize
After that import them into the create_app method and initilize with application
"""
from pyjolt.database import SqlDatabase
from pyjolt.database.migrate import Migrate

from app.authentication import Auth

db: SqlDatabase = SqlDatabase()
migrate: Migrate = Migrate()
auth: Auth = Auth()

__all__ = ["auth", "db", "migrate"]
