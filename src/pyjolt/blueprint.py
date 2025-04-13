"""
Class for creating endpoints which are logically grouped together in a file (blueprint).
The Blueprint instance is registered with the application and it's endpoints are added to the
application. Blueprints can be configures with url prefixes and some other configurations (see docs)
"""
from .common import Common

class Blueprint(Common):
    """
    Blueprint class
    """

    def __init__(self, import_name: str,
                 blueprint_name: str,
                 url_prefix: str = "",
                 static_folder_path: str = None):
        """
        Initilizer for blueprint
        """
        super().__init__()
        self.import_name = import_name
        self.blueprint_name = blueprint_name
        self.url_prefix = url_prefix
        self.static_folder_path = static_folder_path
        self.app = None

    def add_app(self, app):
        """
        Adds application reference to app property of the
        Blueprint instance
        """
        self.app = app
