# request.py
#pylint: disable=C0116
import re
import json
from io import BytesIO
from urllib.parse import parse_qs
from typing import Callable, Any, Union, TYPE_CHECKING, Mapping, cast
import python_multipart as pm

from .response import Response

if TYPE_CHECKING:
    from .pyjolt import PyJolt

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
        app: "PyJolt",
        route_parameters: dict|Mapping,
        route_handler: Callable
    ):
        self._app = app
        self.scope = scope
        self._receive = receive
        self._send: Callable = None  # type: ignore
        self._body: Union[bytes, None] = None
        self._json: Union[dict, None]  = None
        self._form: Union[dict, None]  = None
        self._files: Union[dict, None]  = None
        self._user: Any = None
        self._route_parameters = route_parameters
        self._route_handler    = route_handler
        self._response: Response[Any] = app.response_class(app, self)
        self.state: Any = {}

    @property
    def route_handler(self) -> Callable:
        return self._route_handler

    @property
    def route_parameters(self) -> dict|Mapping:
        return self._route_parameters

    @route_parameters.setter
    def route_parameters(self, rp: dict|Mapping) -> None:
        self._route_parameters = rp

    @property
    def method(self) -> str:
        if self._send is not None:
            return "SOCKET"
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
    def query_params(self) -> dict[str, str]:
        qs = self.scope.get("query_string", b"")
        parsed = parse_qs(qs.decode("utf-8"))
        return cast(dict[str, str], {k: v if len(v) > 1 else v[0] for k, v in parsed.items()})

    @property
    def user(self) -> Any:
        return self._user
    
    @property
    def app(self) -> "PyJolt":
        return self._app

    def set_user(self, user: Any) -> None:
        self._user = user

    def remove_user(self) -> None:
        self._user = None

    async def body(self) -> bytes:
        if self._body is not None:
            return self._body

        parts = []
        while True:
            msg = await self._receive()
            if msg["type"] == "http.request":
                parts.append(msg.get("body", b""))
                if not msg.get("more_body", False):
                    break
        self._body = b"".join(parts)
        return self._body

    async def json(self) -> dict[str, Any]|None:
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

    async def form(self) -> dict[str, Any]:
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
    
    async def send(self, message: dict) -> None:
        if self._send is None:
            raise RuntimeError("Send function is available only on websocket requests")
        return await self._send(message)
    
    def set_send(self, send: Callable) -> None:
        self._send = send
    
    async def receive(self) -> dict:
        if self._send is None:
            raise RuntimeError("Receive function is available only on websocket requests")
        return await self._receive()
    
    async def accept(self) -> None:
        if self._send is None:
            raise RuntimeError("Accept function is available only on websocket requests")
        await self._send({"type": "websocket.accept"})

    async def _parse_multipart(self, content_type: str) -> tuple[dict, dict]:
        """
        Stream the body through python-multipart, collecting fields and files.
        """
        raw = await self.body()
        stream = BytesIO(raw)

        form_data: dict[str, str] = {}
        files:     dict[str, UploadedFile] = {}

        def on_field(field: Any) -> None:
            name = field.field_name
            val  = getattr(field, "value", None)

            if isinstance(name, bytes):
                name = name.decode("latin1")
            if isinstance(val, bytes):
                val = val.decode("utf-8", "replace")

            form_data[name] = cast(str, val)

        def on_file(f: Any) -> None:
            raw_name = getattr(f, "field_name", b"") or b""
            raw_fn   = getattr(f, "file_name", b"") or b""
            name = raw_name.decode("latin1") if isinstance(raw_name, bytes) else raw_name
            fn   = raw_fn.decode("latin1")   if isinstance(raw_fn,   bytes) else raw_fn

            fileobj = f.file_object
            fileobj.seek(0)
            content = fileobj.read()

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

        header_map = {"Content-Type": content_type}

        pm.parse_form(
            headers=cast(dict[str, bytes], header_map),
            input_stream=stream,
            on_field=on_field,
            on_file=on_file,
        )

        return form_data, files

    async def get_data(self, location: str = "json") -> dict[str, Any]|None:
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
    
    @property
    def response(self) -> Response:
        return self._response

    @property
    def res(self) -> Response:
        return self._response
