"""
Utility methods for PyJolt
"""
import importlib.util
import os
import sys
import inspect
import asyncio
from asyncio import Task, Future
from typing import Callable, Any

def get_app_root_path(import_name: str) -> str:
    """
    Finds the root path of the application package on the file system or
    uses the current working directory
    """
    # First, check if the module is already imported and has a __file__ attribute.
    mod = sys.modules.get(import_name)
    if mod is not None and hasattr(mod, "__file__"):
        return os.path.dirname(os.path.abspath(mod.__file__))

    # Tries to load the modules loader
    loader = importlib.util.find_spec(import_name)
    if loader is None or import_name == "__main__":
        return os.getcwd()

    # Checks if loader has a filename
    filepath = None
    if hasattr(loader, "get_filename"):
        filepath = loader.get_filename(import_name)

    # Tries to lookup the loaders path attribute
    if not filepath and hasattr(loader, "path"):
        filepath = loader.path

    if filepath is None:
        #Current working directory fallback
        return os.getcwd()

    # Return the directory name of the absolute path where the module resides.
    return os.path.dirname(os.path.abspath(filepath))

async def run_sync_or_async(func: Callable, *args, **kwargs):
    """
    Support for sync or async methods
    Runs async method directly or a sync method in a threadpool
    """
    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        lambda: func(*args, **kwargs)
    )

def run_in_background(func: Callable[..., Any], *args, executor = None, **kwargs) -> Task|Future:
    """
    Fire-and-forget a function (async or sync) without awaiting its result.
    Useful for sending emails or other longer running tasks that do not
    need to wait for the result.
    """

    # current running event loop
    loop = asyncio.get_running_loop()

    if asyncio.iscoroutinefunction(func):
        # Schedule the async function to run
        return loop.create_task(func(*args, **kwargs))

    # If it's a sync function, run it in the default thread pool executor
    return loop.run_in_executor(executor, func, *args, **kwargs)
