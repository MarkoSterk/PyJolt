"""
App extensions
"""
from pyjolt.database import SqlDatabase
from pyjolt.database.migrate import Migrate
from pyjolt.caching import Cache

db: SqlDatabase = SqlDatabase()
migrate: Migrate = Migrate(db)
cache: Cache = Cache()

__all__ = ['db', 'migrate', 'cache']
