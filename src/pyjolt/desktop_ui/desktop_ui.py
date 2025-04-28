"""
Adds desktop app wrapper to PyJolt application
"""
import sys
import threading
import time
from typing import Callable
import webview
from pystray import MenuItem as Item, Icon
from PIL import Image

from ..pyjolt import PyJolt

class DesktopUI:
    """
    PyJolt app wrapper class. Turns PyJolt web app into a desktop app.
    """

    def __init__(self, app: PyJolt = None):
        """
        Initialize the Desktop UI wrapper.

        :param app: PyJolt app instance
        """
        self._app = None
        self.host = None
        self.port = None
        self.index_route: str = None
        self.lifespan: str = "on"
        self.server_thread = None
        self.tray_icon = None
        self.window = None
        self.window_settings = None
        self.pywebview_functions: list[Callable] = []
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the app instance and configurations."""
        self._app = app
        self.desktop_app_name = self._app.get_conf("APP_NAME", "PyJolt Desktop")
        self.host = self._app.get_conf("HOST", "localhost")
        self.port = self._app.get_conf("PORT", 8080)
        self.index_route = self._app.get_conf("INDEX_ROUTE", "")
        self.lifespan = self._app.get_conf("LIFESPAN", "on")
        self.window_settings = self._app.get_conf("WINDOW_SETTINGS", {})

        self._app.add_extension(self)

        if self.index_route.startswith("/"):
            self.index_route = self.index_route.lstrip("/")

    @property
    def expose(self) -> Callable:
        """
        Decorator to add a function to the frontend via pywebview.
        The functions is registered with pywebview before startup
        """
        def decorator(func: Callable) -> Callable:
            self.pywebview_functions.append(func)
            return func
        return decorator

    def _start_server(self, *args, **kwargs):
        """Runs the PyJolt app using its built-in `.run()` method."""

        print(f"🌐 Starting PyJolt server on http://{self.host}:{self.port}/{self.index_route}")
        self._app.run(host=self.host, port=self.port, reload=False,
            factory=False, lifespan=self.lifespan)

    def _start_webview(self):
        """Launches pywebview as an embedded browser window."""
        url = f"http://{self.host}:{self.port}/{self.index_route}"

        # Load previous size/position if available
        width = self.window_settings.get("width", 1024)
        height = self.window_settings.get("height", 768)
        fullscreen = self.window_settings.get("fullscreen", False)

        # Create a WebView window
        self.window: webview.Window = webview.create_window(
            self.desktop_app_name,
            url,
            width=width,
            height=height,
            fullscreen=fullscreen,
            confirm_close=True,  # Prevent accidental closing
            resizable=True
        )
        #exposes registered python functions to the frontend
        #functions can be calleb with: window.pywebview.func_name
        self.window.expose(*self.pywebview_functions)

        # Run the WebView event loop
        webview.start(self._on_window_close, debug=self._app.get_conf("DEBUG"))

    def _on_window_close(self):
        """Handles WebView window close event."""
        print("🔄 Saving window settings before closing...")
        if self.window:
            self.window_settings.update({
                "width": self.window.width,
                "height": self.window.height,
                "fullscreen": self.window.fullscreen
            })
        print("🛑 Stopping PyJolt server...")
        sys.exit(0)  # Ensure all threads stop when closing the app

    def _start_system_tray(self):
        """Creates a system tray icon with menu options."""
        image = Image.new("RGB", (64, 64), (255, 0, 0))  # Placeholder icon
        menu = (
            Item("Restore", self._restore_from_tray),
            Item("Exit", self._quit_app)
        )
        self.tray_icon = Icon("pyjolt_tray", image, menu=menu)
        self.tray_icon.run()

    def _minimize_to_tray(self, icon, item):
        """Minimizes the app to the system tray."""
        print("Minimizing to tray...")
        if self.window:
            self.window.hide()
        icon.visible = True  # Show the tray icon

    def _restore_from_tray(self, icon, item):
        """Restores the app from the system tray."""
        print("Restoring from tray...")
        if self.window:
            self.window.show()
        icon.visible = False  # Hide the tray icon

    def _quit_app(self, icon, item):
        """Closes the application."""
        print("Exiting application...")
        icon.stop()
        if self.window:
            self.window.destroy()
        sys.exit(0)

    def run(self, *args, **kwargs):
        """Runs the PyJolt app with Uvicorn and opens a WebView-based window."""
        # Start the PyJolt server in a separate thread
        self.server_thread = threading.Thread(target=lambda: self._start_server(*args, **kwargs), daemon=True)
        self.server_thread.start()

        # Wait for the server to start before launching the window
        time.sleep(1)
        print("Platform is: ", sys.platform)
        # Start system tray (only if not on macOS)
        if sys.platform != "darwin":
            tray_thread = threading.Thread(target=self._start_system_tray, daemon=True)
            tray_thread.start()
        else:
            print("System tray integration is disabled on macOS (must run on main thread)")

        # Start WebView window (MUST be on main thread for macOS)
        self._start_webview()
