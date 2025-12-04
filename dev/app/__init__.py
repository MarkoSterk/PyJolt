"""
Entry point for app
"""
from datetime import datetime
from pyjolt import PyJolt, app

from app.configs import Config

@app(__name__, configs=Config)
class App(PyJolt):
    """Main app class"""

    @staticmethod
    def format_datetime(value):
        try:
            dt = datetime.fromisoformat(value)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return value  # fallback if parsing fails
