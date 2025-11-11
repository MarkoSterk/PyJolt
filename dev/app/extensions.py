"""
Application extensions
"""
from pyjolt.database.sql import SqlDatabase
from pyjolt.database.sql.migrate import Migrate

db: SqlDatabase = SqlDatabase()
migrate: Migrate = Migrate(db)
