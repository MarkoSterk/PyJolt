"""
Entry point for app
"""
from pyjolt import PyJolt, app

from app.configs import Config

@app(__name__, configs=Config)
class App(PyJolt):
    """Main app class"""
