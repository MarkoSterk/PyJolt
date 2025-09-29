"""
App extensions
"""
from pyjolt.database import SqlDatabase
from pyjolt.database.migrate import Migrate

db: SqlDatabase = SqlDatabase()
migrate: Migrate = Migrate(db)

__all__ = ['db', 'migrate']
