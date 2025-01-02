"""
request.py
Request class which holds all information about individual requests
"""

import json
from urllib.parse import parse_qs

class Request:
    """
    Request class. Holds all information regarding individual requests.
    """
    def __init__(self, scope, receive, app):
        self.app = app
        self.scope = scope
        self.receive = receive
        self._body = None
        self._json = None
        self._form = None
        self._files = None
        self._user = None

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
        raw_qs = self.scope.get("query_string", b"")
        qs_str = raw_qs.decode("utf-8")
        parsed = parse_qs(qs_str)
        return {k: v if len(v) > 1 else v[0] for k, v in parsed.items()}
    
    @property
    def user(self) -> None|object:
        """
        Returns authenticated user or None
        """
        return self._user

    async def  set_user(self, user: None|object) -> None:
        """
        Sets the user on the current request object
        """
        self._user = user

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

    async def _parse_multipart(self, content_type: str):
        """Parses multipart/form-data and separates fields and files."""
        raw_body = await self.body()

        # Extract boundary from content-type
        boundary = content_type.split("boundary=")[-1]
        boundary = boundary.strip()

        form_data = {}
        files = {}

        # Split body into parts based on the boundary
        boundary_bytes = f"--{boundary}".encode("utf-8")
        end_boundary_bytes = f"--{boundary}--".encode("utf-8")

        parts = raw_body.split(boundary_bytes)
        for part in parts:
            # Skip empty or end boundaries
            part = part.strip()
            if not part or part == end_boundary_bytes:
                continue

            # Separate headers and content
            headers, _, content = part.partition(b"\r\n\r\n")
            headers = headers.decode("utf-8").split("\r\n")
            content = content.rstrip(b"\r\n")

            # Parse headers into a dictionary
            header_dict = {}
            for header in headers:
                if ":" in header:
                    name, value = header.split(":", 1)
                    header_dict[name.strip().lower()] = value.strip()

            # Parse content-disposition
            content_disposition = header_dict.get("content-disposition", "")
            disposition_params = {}
            for item in content_disposition.split(";"):
                if "=" in item:
                    key, value = item.split("=", 1)
                    disposition_params[key.strip()] = value.strip('"')

            name = disposition_params.get("name")
            filename = disposition_params.get("filename")

            if name:
                if filename:
                    # This is a file field
                    files[name] = {
                        "filename": filename,
                        "content": content,
                        "content_type": header_dict.get("content-type", "application/octet-stream"),
                    }
                else:
                    # This is a regular form field
                    form_data[name] = content.decode("utf-8")

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
        return None
