"""
App extensions
"""
from pyjolt.database.sql import SqlDatabase
from pyjolt.database.sql.migrate import Migrate
from pyjolt.caching import Cache
from pyjolt.database.nosql import NoSqlDatabase

db: SqlDatabase = SqlDatabase()
migrate: Migrate = Migrate(db)
cache: Cache = Cache()
nosqldb: NoSqlDatabase = NoSqlDatabase()

__all__ = ['db', 'migrate', 'cache', 'nosqldb']
