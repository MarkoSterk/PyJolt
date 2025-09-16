"""
OpenAPI controller
"""
from pydantic import BaseModel
from typing import Any, TYPE_CHECKING, Dict, Optional, Type, Set

from .http_statuses import HttpStatus
from .media_types import MediaType
from .response import Response
from .request import Request
from .controller import Controller, get, produces
from .controller.utilities import _extract_response_type

if TYPE_CHECKING:
    from .pyjolt import PyJolt

class OpenApiSpecs(BaseModel):

    openapi: str = "3.0.3"
    info: Any = None
    servers: Any = None
    paths: Any = None
    components: Any = None

class OpenAPIController(Controller):

    @get("/specs.json", open_api_spec=False)
    @produces(MediaType.APPLICATION_JSON)
    async def specs(self, req: Request) -> Response[OpenApiSpecs]:
        return req.response.json(self.app.json_spec).status(HttpStatus.OK)

    @get("/docs", open_api_spec=False)
    @produces(MediaType.TEXT_HTML)
    async def docs(self, req: Request) -> Response:
        return (await req.response.html_from_string("""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Swagger UI</title>
                <link rel="stylesheet"
                      href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.18.3/swagger-ui.css" />
            </head>
            <body>
                <div id="swagger-ui"></div>
                <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.18.3/swagger-ui-bundle.js"></script>
                <script>
                    const ui = SwaggerUIBundle({
                        url: '{{ url_for("OpenAPIController.specs") }}',
                        dom_id: '#swagger-ui',
                    })
                </script>
            </body>
        </html>
        """)).status(HttpStatus.OK)



def _as_media_type(mt: Any) -> str:
    # Accept enum-ish (with .value) or plain str
    if mt is None:
        return "application/json"
    return getattr(mt, "value", str(mt))

def _as_status_code(http_status: HttpStatus) -> str:
    if isinstance(http_status, HttpStatus):
        return http_status.value
    return http_status

def _model_name(model: Type) -> str:
    # Pick a stable schema key
    return getattr(model, "__name__", "AnonymousModel")

def _pydantic_schema_dict(model: Optional[Type]) -> Optional[Dict[str, Any]]:
    if model is None:
        return None
    # Pydantic v2
    if hasattr(model, "model_json_schema"):
        try:
            return model.model_json_schema(ref_template="#/components/schemas/{model}")
        except TypeError:
            # older/stricter signatures
            return model.model_json_schema()
    # Pydantic v1
    if hasattr(model, "schema"):
        try:
            return model.schema(ref_template="#/components/schemas/{model}")
        except TypeError:
            return model.schema()
    # Fallback – unknown object
    return {"type": "object"}

def _ensure_schema(components: Dict[str, Any], model: Optional[Type]) -> Optional[Dict[str, Any]]:
    if model is None:
        return None
    name = _model_name(model)
    if "schemas" not in components:
        components["schemas"] = {}
    if name not in components["schemas"]:
        components["schemas"][name] = _pydantic_schema_dict(model) or {"type": "object"}
    # Return a $ref to the component
    return {"$ref": f"#/components/schemas/{name}"}


def build_openapi(
    controllers: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]],
    *,
    title: str,
    version: str,
    openapi_version: str,
    servers: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """
    controllers structure:
    {
        "<base_path>": {
            "<HTTP_METHOD>": {
                "<endpoint_path>": {
                    "method": <callable>,
                    "produces": <MediaType>,
                    "consumes": <MediaType>,
                    "consumes_type": <PydanticModel>,
                    "response_type": <PydanticModel>,            # optional
                    "default_status_code": <HttpStatus>,
                    "http_method": <HTTP_METHOD>,
                    "path": <endpoint_path>,
                    "base_path": <base_path>,
                    "summary": <string>,                          # optional
                    "description": <string>,                      # optional
                    "tags": [<string>, ...],                      # optional
                    "operation_id": <string>,                     # optional
                    "error_responses": [<Descriptor>, ...]
                }
            }
        }
    }

    Descriptor has: media_type, body, description, status (default BAD_REQUEST).
    """
    spec: Dict[str, Any] = {
        "openapi": openapi_version,
        "info": {"title": title, "version": version, "description": ""},
        "paths": {},
        "components": {"schemas": {}},
    }
    if servers:
        spec["servers"] = [{"url": url} for url in servers]

    components = spec["components"]
    paths = spec["paths"]

    # Keep track of models we referenced to ensure they land in components
    referenced_models: Set[Type] = set()
    for base_path, controller in controllers.items():
        for http_method, endpoints_map in controller.endpoints_map.items():
            for endpoint_path, ep_cfg in endpoints_map.items():
                if not ep_cfg.get("open_api_spec"):
                    continue
                # Compute the final OpenAPI path (base_path + endpoint_path)
                # Normalize slashes
                full_path = f"/{base_path.strip('/')}/{endpoint_path.strip('/')}".replace("//", "/")
                if base_path == "/":
                    full_path = f"/{endpoint_path.strip('/')}" or "/"

                if full_path not in paths:
                    paths[full_path] = {}

                op_obj: Dict[str, Any] = {}
                paths[full_path][http_method.lower()] = op_obj

                # Summary / description via dict.get(..., "")
                op_obj["summary"] = ep_cfg.get("summary", "")
                op_obj["description"] = ep_cfg.get("method").__doc__ or ep_cfg.get("description", "")
                # Tags: explicit or fallback to first segment of base_path
                op_obj["tags"] = ep_cfg.get("tags", "")

                # operationId (optional but useful)
                op_obj["operationId"] = ep_cfg.get("method").__name__ or (
                    f"{http_method.lower()}_{base_path.strip('/').replace('/','_')}_{endpoint_path.strip('/').replace('/','_')}"
                    or f"{http_method.lower()}_root"
                )

                # Request body
                consumes = ep_cfg.get("consumes")
                consumes_type = ep_cfg.get("consumes_type")
                if consumes or consumes_type:
                    mt = _as_media_type(consumes) if consumes else "application/json"
                    schema_ref = _ensure_schema(components, consumes_type)
                    if consumes_type:
                        try:
                            referenced_models.add(consumes_type)
                        except TypeError:
                            pass
                    request_body = {
                        "required": True if consumes_type else False,
                        "content": {
                            mt: {
                                "schema": schema_ref or {"type": "object"}
                            }
                        }
                    }
                    op_obj["requestBody"] = request_body

                # Responses (success/default)
                produces = ep_cfg.get("produces")
                mt_out = _as_media_type(produces) if produces else "application/json"
                default_status = _as_status_code(ep_cfg.get("default_status_code", 200))
                responses: Dict[str, Any] = {}
                op_obj["responses"] = responses

                # Optional explicit response model
                response_type = _extract_response_type(ep_cfg.get("method"))
                resp_schema_ref = _ensure_schema(components, response_type) if response_type else None
                if response_type:
                    try:
                        referenced_models.add(response_type)
                    except TypeError:
                        pass

                responses[default_status] = {
                    "description": ep_cfg.get("description", "") or "",
                    "content": {
                        mt_out: {"schema": resp_schema_ref or {"type": "object"}}
                    }
                }

                # Error responses (merge by status code if repeated)
                for desc in ep_cfg.get("error_responses", []) or []:
                    status_code = _as_status_code(getattr(desc, "status", None) or getattr(desc, "status_code", 400))
                    emt = _as_media_type(getattr(desc, "media_type", None))
                    body_model = getattr(desc, "body", None)
                    err_desc = getattr(desc, "description", None) or ""

                    schema_ref = _ensure_schema(components, body_model)
                    if body_model:
                        try:
                            referenced_models.add(body_model)
                        except TypeError:
                            pass

                    # Initialize or merge
                    if status_code not in responses:
                        responses[status_code] = {"description": err_desc or "", "content": {}}
                    # If description is empty, fill it
                    if not responses[status_code].get("description"):
                        responses[status_code]["description"] = err_desc or ""

                    responses[status_code]["content"][emt] = {
                        "schema": schema_ref or {"type": "object"}
                    }

    return spec