"""
App extensions
"""
from pyjolt.database import SqlDatabase
from pyjolt.database.migrate import Migrate
from pyjolt.caching import Cache

from app.authentication import Auth
from app.scheduler import Scheduler
from app.ai_interface import Interface

db: SqlDatabase = SqlDatabase()
migrate: Migrate = Migrate()
auth: Auth = Auth()
scheduler: Scheduler = Scheduler()
cache: Cache = Cache()
ai_interface: Interface = Interface()

__all__ = ['db', 'migrate', 'auth', 'scheduler', 'cache', 'ai_interface']
