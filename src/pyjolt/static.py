"""
Default static endpoint that serves all static files for the application
In production, static files should be serves directly by a reverse proxy server such
as Nginx. This reverse proxy server approach is more efficient
"""
import os
import re
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

async def get_range_file(res, file_path: str, range_header: str, content_type: str):
    """Returns a ranged response"""
    total = os.path.getsize(file_path)
    m = re.match(r"bytes=(\d+)-(\d*)", range_header)
    if not m:
        start, end, status = 0, total - 1, 200
    else:
        start = int(m.group(1))
        end   = int(m.group(2)) if m.group(2) else total - 1
        end   = min(end, total - 1)
        if start > end:
            raise StaticAssetNotFound()
        status = 206

    length = end - start + 1
    headers = {
        "Content-Type":   content_type,
        "Accept-Ranges":  "bytes",
        "Content-Length": str(length),
        "Cache-Control":  "public, max-age=300",
        "ETag": f'"{os.path.getmtime(file_path):.0f}-{length}"'
    }
    if status == 206:
        headers["Content-Range"] = f"bytes {start}-{end}/{total}"

    # **Don’t** read the bytes here.  Just stash info on `res`.  
    res.status(status)
    # merge headers onto res.headers
    res.headers.update(headers)
    # mark zero-copy parameters
    res.set_zero_copy({
        "file_path": file_path,
        "start":      start,
        "length":     length
    })
    return res

async def static(req, res, path: str):
    """
    Endpoint for static files with HTTP Range support,
    falling back to get_file for full-content requests.
    """
    # Checks if file exists
    file_path = None
    for static_root in req.app.static_files_path:
        candidate = safe_join(static_root, path)
        if candidate and os.path.exists(candidate):
            file_path = candidate
            break
    if not file_path:
        raise StaticAssetNotFound()

    # checks/guesses mimetype
    guessed, _ = mimetypes.guess_type(file_path)
    content_type = guessed or "application/octet-stream"

    # Checks range header and returns range if header is present
    range_header = req.headers.get("range")
    if not range_header:
        status, headers, body = await get_file(file_path, content_type=content_type)
        headers["Accept-Ranges"] = "bytes"
        return res.send_file(body, headers).status(status)

    return await get_range_file(res, file_path, range_header, content_type)
    



# async def static(req, res, path: str):
#     """
#     Endpoint for static files
#     """
#     file_path: str = None
#     for static_file_path in req.app.static_files_path:
#         file_path = safe_join(static_file_path, path)
#         if file_path is not None and os.path.exists(file_path):
#             break
#         file_path = None
#     if file_path is None:
#         # pylint: disable-next=E0710
#         raise StaticAssetNotFound()

#     status, headers, body = await get_file(file_path)
#     return res.send_file(body, headers).status(status)
