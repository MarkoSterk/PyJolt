"""
Test app implementation
"""

from pyjolt import PyJolt, app, on_startup, on_shutdown, app_path

from app.configs import Config

@app_path("/ecris")
@app(__name__, configs = Config)
class Application(PyJolt):
    
    @on_startup
    async def first_startup_method(self):
        print("Starting up...", self.url_for("Static.get", filename="image.png"))
    
    @on_shutdown
    async def first_shutdown_method(self):
        print("Shuting down...", self.url_for("Static.get", filename="image.png"))
