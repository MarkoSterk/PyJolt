"""
Application extensions
"""
from pyjolt.database.sql import SqlDatabase
from pyjolt.database.sql.migrate import Migrate
from pyjolt.email import EmailClient
from pyjolt.caching import Cache

db: SqlDatabase = SqlDatabase()
migrate: Migrate = Migrate(db)
email: EmailClient = EmailClient()
second_email: EmailClient = EmailClient(configs_name="SECOND_EMAIL")
cache: Cache = Cache()

other_db: SqlDatabase = SqlDatabase(db_name="other_db", configs_name="OTHER_DB")
other_migrate: Migrate = Migrate(other_db)
