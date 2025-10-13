"""
App extensions
"""
from pyjolt.database.sql import SqlDatabase
from pyjolt.database.sql.migrate import Migrate

from pyjolt.database.nosql import NoSqlDatabase

db: SqlDatabase = SqlDatabase()
migrate: Migrate = Migrate(db)
nosqldb: NoSqlDatabase = NoSqlDatabase()

__all__ = ['db', 'migrate', 'nosqldb']
