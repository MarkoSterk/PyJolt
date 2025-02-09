"""
PyScript extension for PyJolt.
"""
import os
from ..pyjolt import PyJolt

class PyScript:
    """
    Extension class for PyJolt. Add a new static path and url
    for serving PyScript static assets
    """

    def __init__(self, app: PyJolt = None):
        self._app: PyJolt = None
        self._files_path: str = None
        self._static_url: str = None
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: PyJolt):
        """Initilizer for extension"""
        self._app = app
        self._static_url: str = self._app.get_conf("PYSCRIPT_STATIC_URL", "pyscript")
        self._files_path = os.path.join(os.path.dirname(__file__))
        self._app.add_static_files_path(self._files_path)
