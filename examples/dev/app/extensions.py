"""
App extensions
"""
from pyjolt.database import SqlDatabase
from pyjolt.database.migrate import Migrate
from pyjolt.caching import Cache

from app.authentication import Auth
from app.scheduler import Scheduler

db: SqlDatabase = SqlDatabase()
migrate: Migrate = Migrate()
auth: Auth = Auth()
scheduler: Scheduler = Scheduler()
cache: Cache = Cache()

__all__ = ['db', 'migrate', 'auth', 'scheduler', 'cache']
