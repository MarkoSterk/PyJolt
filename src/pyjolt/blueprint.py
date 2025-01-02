"""
Class for creating endpoints which are logically grouped together in a file (blueprint).
The Blueprint instance is registered with the application and it's endpoints are added to the
application. Blueprints can be configures with url prefixes and some other configurations (see docs)
"""
from .common import Common
from .router import Router

class Blueprint(Common):
    """
    Blueprint class
    """

    def __init__(self, import_name: str,
                 blueprint_name: str,
                 url_prefix: str = ""):
        """
        Initilizer for blueprint
        """
        self.import_name = import_name
        self.blueprint_name = blueprint_name
        self.url_prefix = url_prefix
        self.router = Router()
