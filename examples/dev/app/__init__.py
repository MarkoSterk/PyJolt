"""
Test app implementation
"""
from app.configs import Config
from pyjolt import PyJolt


def create_app(configs = Config) -> PyJolt:
    """App factory"""
    app: PyJolt = PyJolt(__name__, "PyJolt Test")
    app.configure_app(configs)

    return app
