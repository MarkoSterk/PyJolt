"""
request.py
Request class which holds all information about individual requests
"""
from io import BytesIO
import json
from urllib.parse import parse_qs
from typing import Callable
from multipart.multipart import parse_form
from multipart.multipart import parse_options_header


class UploadedFile:
    """
    Class for uploaded files
    """
    def __init__(self, filename: str, content: bytes, content_type: str):
        self.filename = filename
        self.content_type = content_type
        self._content = content
        self._stream = BytesIO(content)

    #pylint: disable-next=C0116
    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)

    #pylint: disable-next=C0116
    def seek(self, pos: int, whence: int = 0) -> int:
        return self._stream.seek(pos, whence)

    #pylint: disable-next=C0116
    def save(self, path: str):
        with open(path, "wb") as f:
            self.seek(0)
            f.write(self._stream.read())

    @property
    #pylint: disable-next=C0116
    def size(self) -> int:
        current_pos = self._stream.tell()
        self._stream.seek(0, 2)  # Move to end
        size = self._stream.tell()
        self._stream.seek(current_pos)  # Restore position
        return size
    
    @property
    #pylint: disable-next=C0116
    def stream(self):
        self.seek(0)
        return self._stream

    def get_stream(self) -> BytesIO:
        """Returns a fresh BytesIO stream each time."""
        return BytesIO(self._content)

    def __repr__(self):
        return f"<UploadedFile filename={self.filename} size={self.size} content_type={self.content_type}>"


class Request:
    """
    Request class. Holds all information regarding individual requests.
    """
    def __init__(self, scope: dict,
                 receive, app,
                 route_parameters: dict,
                 route_handler: Callable):
        self.app = app
        self.scope = scope
        self.receive = receive
        self._body = None
        self._json = None
        self._form = None
        self._files = None
        self._user = None
        self._route_parameters = route_parameters
        self._route_handler = route_handler

    @property
    def route_handler(self) -> Callable:
        """
        Returns route handler
        """
        return self._route_handler

    @property
    def route_parameters(self) -> dict:
        """
        Getter for route parameters
        """
        return self._route_parameters

    @route_parameters.setter
    def route_parameters(self, route_parameters: dict) -> None:
        """
        Setter for route parameters
        """
        self._route_parameters = route_parameters

    @property
    def method(self) -> str:
        """
        Getter for request method
        """
        return self.scope.get("method", "").upper()

    @property
    def path(self) -> str:
        """
        Getter for request path (route path)
        """
        return self.scope.get("path", "/")
    
    @property
    def query_string(self) -> str:
        """
        Returns query parameters as string
        """
        return self.scope.get("query_string", b"{}").decode("utf-8")

    @property
    def headers(self) -> dict:
        """
        Converts the headers list of tuples into a dictionary with string keys and values.
        """
        raw_headers = self.scope.get("headers", [])
        return {key.decode("latin1").lower(): value.decode("latin1") for key, value in raw_headers}

    @property
    def query_params(self) -> dict:
        """
        Getter for request query parameters
        """
        raw_qs = self.scope.get("query_string", b"{}")
        qs_str = raw_qs.decode("utf-8")
        parsed = parse_qs(qs_str)
        return {k: v if len(v) > 1 else v[0] for k, v in parsed.items()}

    @property
    def user(self) -> None|object:
        """
        Returns authenticated user or None
        """
        return self._user

    def set_user(self, user: None|object) -> None:
        """
        Sets the user on the current request object
        """
        self._user = user
    
    def remove_user(self) -> None:
        """
        Removes user
        """
        self._user = None

    async def body(self) -> bytes:
        """Reads the raw body once and caches it."""
        if self._body is not None:
            return self._body

        body_chunks = []
        while True:
            message = await self.receive()
            if message["type"] == "http.request":
                body_chunks.append(message.get("body", b""))
                if not message.get("more_body", False):
                    break
        self._body = b"".join(body_chunks)
        return self._body

    async def json(self) -> dict:
        """Parses the body as JSON and caches the result."""
        if self._json is not None:
            return self._json

        raw_body = await self.body()
        if not raw_body:
            return None
        try:
            self._json = json.loads(raw_body)
        except json.JSONDecodeError:
            self._json = None
        return self._json

    async def form(self) -> dict:
        """Parses the body as form data (application/x-www-form-urlencoded or multipart/form-data)."""
        if self._form is not None:
            return self._form
        content_type = self.headers.get("content-type", "")

        if "multipart/form-data" in content_type:
            self._form, self._files = await self._parse_multipart(content_type)
        elif "application/x-www-form-urlencoded" in content_type:
            # Parse urlencoded form data
            raw_body = await self.body()
            self._form = parse_qs(raw_body.decode("utf-8"))
            self._form = {k: v if len(v) > 1 else v[0] for k, v in self._form.items()}
        else:
            self._form = {}

        return self._form

    async def files(self) -> dict:
        """Returns parsed file data from multipart form-data."""
        if self._files is None:
            await self.form()  # Ensure form is parsed
        return self._files or {}

    async def form_and_files(self) -> dict:
        """Returns form and files data"""
        return await self.get_data("form_and_files")

    async def _parse_multipart(self, content_type: str):
        """
        Parses multipart/form-data using python-multipart's low-level API.
        """
        raw_body = await self.body()
        stream = BytesIO(raw_body)

        # Extract boundary correctly
        _, params = parse_options_header(content_type)
        boundary = params.get(b"boundary")
        if not boundary:
            raise ValueError("No boundary found in Content-Type")

        form_data = {}
        files = {}

        def on_field(name: bytes, value: bytes):
            form_data[name.decode()] = value.decode()

        def on_file(name: bytes, file):
            # The file object has .filename, .content_type, and .file (stream)
            files[name.decode()] = UploadedFile(
                filename=file.filename.decode(),
                content=file.file.read(),
                content_type=file.content_type.decode()
            )

        parse_form(
            headers={b"content-type": content_type.encode()},
            input_stream=stream,
            on_field=on_field,
            on_file=on_file
        )

        return form_data, files


    async def get_data(self, location: str = "json"):
        """Returns request data from provided location or None"""
        if location == "json":
            return await self.json()
        if location == "form":
            return await self.form()
        if location == "files":
            return await self.files()
        if location == "form_and_files":
            form_data = await self.form()
            files_data = await self.files()
            return {**form_data, **files_data}
        if location == "query":
            return self.query_params
        return None
