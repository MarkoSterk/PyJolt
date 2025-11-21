"""
Application extensions
"""
from pyjolt.database.sql import SqlDatabase
from pyjolt.database.sql.migrate import Migrate
from pyjolt.email import EmailClient

db: SqlDatabase = SqlDatabase()
migrate: Migrate = Migrate(db)
email: EmailClient = EmailClient()