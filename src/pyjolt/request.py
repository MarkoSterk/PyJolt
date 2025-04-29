# request.py
#pylint: disable=C0116
import re
import json
from io import BytesIO
from urllib.parse import parse_qs
from typing import Callable, Any, Union
from multipart.multipart import File
from multipart.multipart import parse_form

def extract_boundary(content_type: str) -> str:
    """
    Pull the boundary=... out of a Content-Type header.
    """
    match = re.search(r'boundary="?([^";]+)"?', content_type)
    if not match:
        raise ValueError("No boundary found in Content-Type")
    return match.group(1)

class UploadedFile:
    """
    Wrapper around an in-memory/temporary file.
    """
    def __init__(self, filename: str, content: bytes, content_type: str):
        self.filename = filename
        self.content_type = content_type
        self._content = content
        self._stream = BytesIO(content)

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)

    def seek(self, pos: int, whence: int = 0) -> int:
        return self._stream.seek(pos, whence)

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            self.seek(0)
            f.write(self._stream.read())

    @property
    def size(self) -> int:
        cur = self._stream.tell()
        self._stream.seek(0, 2)
        sz = self._stream.tell()
        self._stream.seek(cur)
        return sz

    @property
    def stream(self) -> BytesIO:
        self.seek(0)
        return self._stream

    def get_stream(self) -> BytesIO:
        return BytesIO(self._content)

    def __repr__(self) -> str:
        return (f"<UploadedFile filename={self.filename!r} "
                f"size={self.size} content_type={self.content_type!r}>")

class Request:
    """
    ASGI-style request adapter that lazy-parses JSON, form, and multipart.
    """
    def __init__(
        self,
        scope: dict,
        receive: Callable[..., Any],
        app: Any,
        route_parameters: dict,
        route_handler: Callable
    ):
        self.app = app
        self.scope = scope
        self.receive = receive
        self._body:       Union[bytes, None] = None
        self._json:       Union[dict, None]  = None
        self._form:       Union[dict, None]  = None
        self._files:      Union[dict, None]  = None
        self._user:       Any                = None
        self._route_parameters = route_parameters
        self._route_handler    = route_handler

    @property
    def route_handler(self) -> Callable:
        return self._route_handler

    @property
    def route_parameters(self) -> dict:
        return self._route_parameters

    @route_parameters.setter
    def route_parameters(self, rp: dict) -> None:
        self._route_parameters = rp

    @property
    def method(self) -> str:
        return self.scope.get("method", "").upper()

    @property
    def path(self) -> str:
        return self.scope.get("path", "/")

    @property
    def query_string(self) -> str:
        return self.scope.get("query_string", b"").decode("utf-8")

    @property
    def headers(self) -> dict[str, str]:
        """
        Decode the raw ASGI headers into a dict of lowercase str→str.
        """
        raw = self.scope.get("headers", [])
        return {
            key.decode("latin1").lower(): val.decode("latin1")
            for key, val in raw
        }

    @property
    def query_params(self) -> dict:
        qs = self.scope.get("query_string", b"")
        parsed = parse_qs(qs.decode("utf-8"))
        return {k: v if len(v) > 1 else v[0] for k, v in parsed.items()}

    @property
    def user(self) -> Any:
        return self._user

    def set_user(self, user: Any) -> None:
        self._user = user

    def remove_user(self) -> None:
        self._user = None

    async def body(self) -> bytes:
        if self._body is not None:
            return self._body

        parts = []
        while True:
            msg = await self.receive()
            if msg["type"] == "http.request":
                parts.append(msg.get("body", b""))
                if not msg.get("more_body", False):
                    break
        self._body = b"".join(parts)
        return self._body

    async def json(self) -> Union[dict, None]:
        if self._json is not None:
            return self._json
        raw = await self.body()
        if not raw:
            return None
        try:
            self._json = json.loads(raw)
        except json.JSONDecodeError:
            self._json = None
        return self._json

    async def form(self) -> dict:
        if self._form is not None:
            return self._form

        ct = self.headers.get("content-type", "")
        if "multipart/form-data" in ct:
            self._form, self._files = await self._parse_multipart(ct)
        elif "application/x-www-form-urlencoded" in ct:
            raw = await self.body()
            parsed = parse_qs(raw.decode("utf-8"))
            self._form = {k: v if len(v) > 1 else v[0] for k, v in parsed.items()}
        else:
            self._form = {}

        return self._form

    async def files(self) -> dict[str, UploadedFile]:
        if self._files is None:
            await self.form()
        return self._files or {}

    async def form_and_files(self) -> dict[str, Any]:
        f = await self.form()
        fs = await self.files()
        return {**f, **fs}

    async def _parse_multipart(self, content_type: str) -> tuple[dict, dict]:
        """
        Stream the body through python-multipart, collecting fields and files.
        """
        raw = await self.body()
        stream = BytesIO(raw)

        form_data: dict[str, str] = {}
        files:     dict[str, UploadedFile] = {}

        def on_field(field):
            # field.field_name  (bytes or str)
            val = field.value if hasattr(field, "value") else field.value  # .value is bytes/str
            name = field.field_name
            if isinstance(name, bytes):
                name = name.decode("latin1")
            if isinstance(val, bytes):
                val = val.decode("utf-8", "replace")
            form_data[name] = val

        def on_file(f: File):
            # f: python-multipart File instance
            # f.field_name()   → bytes | None
            # f.file_name()    → bytes | None
            # f.file_object()  → file-like (BytesIO or temp file)
            # f.headers        → dict[bytes, bytes] of part headers
            raw_name = f.field_name or b""
            raw_fn   = f.file_name or b""
            name = raw_name.decode("latin1") if isinstance(raw_name, bytes) else raw_name
            fn   = raw_fn.decode("latin1")   if isinstance(raw_fn,   bytes) else raw_fn

            # read the entire contents
            fileobj = f.file_object
            fileobj.seek(0)
            content = fileobj.read()

            # pull the part’s Content-Type header if it exists
            part_ct = ""
            hdrs = getattr(f, "headers", {})
            if isinstance(hdrs, dict):
                c = hdrs.get(b"Content-Type") or hdrs.get("Content-Type")
                if isinstance(c, bytes):
                    part_ct = c.decode("latin1")
                elif isinstance(c, str):
                    part_ct = c

            files[name] = UploadedFile(
                filename=fn,
                content=content,
                content_type=part_ct
            )

        # python-multipart wants a mapping with .get("Content-Type")
        header_map = {"Content-Type": content_type}

        parse_form(
            headers=header_map,
            input_stream=stream,
            on_field=on_field,
            on_file=on_file
        )

        return form_data, files

    async def get_data(self, location: str = "json") -> Any:
        if location == "json":
            return await self.json()
        if location == "form":
            return await self.form()
        if location == "files":
            return await self.files()
        if location == "form_and_files":
            return await self.form_and_files()
        if location == "query":
            return self.query_params
        return None
