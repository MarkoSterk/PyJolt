"""
PyScript extension for PyJolt.
"""
import os
import json
import shutil

from werkzeug.utils import safe_join

from ..pyjolt import PyJolt
from ..blueprint import Blueprint
from ..static import get_file
from ..exceptions.http_exceptions import StaticAssetNotFound

def register_db_commands(app: PyJolt, pyscript: 'PyScript'):
    """
    Registers subparsers (CLI commands) for pyscript project management migrations to the app's CLI.
    """

    # db-init
    pyscript_init = app.subparsers.add_parser("pyscript-init", help="Initialize a new Pyscript project.")
    pyscript_init.set_defaults(func=lambda args: pyscript.init())

class PyScript:
    """
    Extension class for PyJolt. Add a new static path and url
    for serving PyScript static assets
    """

    _configs_json: str = '{"packages": ["arrr"]}'

    def __init__(self, app: PyJolt = None):
        self._app: PyJolt = None
        self._root_path: str = None
        self._files_path: str = None
        self._static_url: str = None
        self._blueprint_name: str = None
        self._blueprint: Blueprint = None
        self._pyscript_project_path: str = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app: PyJolt):
        """Initilizer for extension"""
        self._app = app
        self._root_path = self._app.root_path
        self._blueprint_name = self._app.get_conf("PYSCRIPT_BLUEPRINT_NAME", "pyscript")
        self._url: str = self._app.get_conf("PYSCRIPT_STATIC_URL", "/pyscript")
        self._files_path = os.path.join(os.path.dirname(__file__), "source_files")
        self._blueprint = Blueprint(__name__, self._blueprint_name, self._url)
        self._pyscript_project_path = os.path.join(self._root_path, self._app.get_conf("PYSCRIPT_PROJECT_PATH", "pyscript"))
        get_decorator = self._blueprint.get("/<path:path>", openapi_ignore=True)
        get_decorator(self.static)

        self._app.register_blueprint(self._blueprint)
        register_db_commands(self._app, self)

    async def static(self, req, res, path: str):
        """
        Endpoint for static files
        """
        file_path: str = None
        for static_path in [self._files_path, self._pyscript_project_path]:
            file_path = safe_join(static_path, path)
            if file_path is not None and os.path.exists(file_path):
                break
            file_path = None

        if file_path is None:
            raise StaticAssetNotFound()

        status, headers, body = await get_file(file_path)
        return res.send_file(body, headers).status(status)

    def init(self):
        """
        Initializes a new PyScript project and creates a new folder at <PYSCRIPT_PROJECT_PATH>.
        """
        if not os.path.exists(self._pyscript_project_path):
            os.makedirs(self._pyscript_project_path)
        else:
            print(f"ERROR: PyScript project at path {self._pyscript_project_path} already exists.")
            return
        with open(f"{self._pyscript_project_path}/pyscript.json", "w", encoding="utf-8") as file:
            json_configs = json.loads(self._configs_json)
            file.write(json.dumps(json_configs, indent=4))
        os.mkdir(os.path.join(self._pyscript_project_path, "src"))
        template_path = os.path.join(os.path.dirname(__file__), "source_files", "template_main.py")
        destination_path = os.path.join(self._pyscript_project_path, "src", "main.py")
        shutil.copy(template_path, destination_path)
