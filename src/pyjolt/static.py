"""
Default static endpoint that serves all static files for the application
In production, static files should be serves directly by a reverse proxy server such
as Nginx. This reverse proxy server approach is more efficient
"""
import os
import mimetypes
import aiofiles
from werkzeug.utils import safe_join

from .exceptions import StaticAssetNotFound

async def get_file(path: str, filename: str = None, content_type: str = None):
    """
    Asynchronously opens the file at `path`.
    - `filename` is optional (used for Content-Disposition).
    - `content_type` is optional (guess using `mimetypes` if not provided).
    
    Returns a tuple (status_code, headers, body_bytes).
    """

    # Guess the MIME type if none is provided
    guessed_type, _ = mimetypes.guess_type(path)
    content_type = content_type or (guessed_type or "application/octet-stream")

    headers = {
        "Content-Type": content_type
    }
    if filename:
        # For file download if filename is provided
        headers["Content-Disposition"] = f'attachment; filename="{filename}"'

    try:
        async with aiofiles.open(path, mode="rb") as f:
            data = await f.read()
    except FileNotFoundError:
        # pylint: disable-next=W0707,E0710
        raise StaticAssetNotFound()

    return 200, headers, data


async def static(req, res, path: str):
    """
    Endpoint for static files
    """
    file_path: str = None
    for static_file_path in req.app.static_files_path:
        file_path = safe_join(static_file_path, path)
        if file_path is not None and os.path.exists(file_path):
            break
        file_path = None
    if file_path is None:
        # pylint: disable-next=E0710
        raise StaticAssetNotFound()

    status, headers, body = await get_file(file_path)
    return res.send_file(body, headers).status(status)
