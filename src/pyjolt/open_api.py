"""
OpenAPI/Swagger interface with support for BOTH Marshmallow and Pydantic schemas.
"""
from typing import Optional
from pydantic import BaseModel as PydanticBaseModel
from .pyjolt import Request, Response, Blueprint


# ------------------------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------------------------

def is_pydantic_model(schema_cls) -> bool:
    """
    Returns True if 'schema_cls' is a Pydantic BaseModel subclass.
    """
    return isinstance(schema_cls, type) and issubclass(schema_cls, PydanticBaseModel)

def generate_openapi_json_schema(schema_cls) -> dict:
    """
    Given a schema class (Marshmallow or Pydantic), produce a JSON Schema dict
    suitable for embedding in an OpenAPI spec.

    - Marshmallow: uses `marshmallow_jsonschema.JSONSchema().dump(...)`
    - Pydantic: uses the built-in `.schema()` method.

    Note: This example uses Pydantic v1 style, which emits 'definitions'. If you
    are on Pydantic v2 and get '$defs' instead, you'll need to remap '$defs'
    to 'definitions' here.
    """
    # if is_marshmallow_schema(schema_cls):
    #     # Instantiate and convert to JSON Schema via marshmallow_jsonschema
    #     return JSONSchema().dump(schema_cls())

    if is_pydantic_model(schema_cls):
        # Pydantic v1 or v2: produce the JSON Schema
        raw_schema = schema_cls.schema()

        # If you're using Pydantic v2, you might see '$defs' instead of 'definitions'
        # If so, convert them for consistency with the Marshmallow approach.
        if "$defs" in raw_schema:
            if "definitions" not in raw_schema:
                raw_schema["definitions"] = {}
            raw_schema["definitions"].update(raw_schema.pop("$defs"))

        return raw_schema

    raise TypeError(f"Unsupported schema class: {schema_cls}")


# ------------------------------------------------------------------------------
# Handlers for Serving the OpenAPI JSON and Swagger UI
# ------------------------------------------------------------------------------

async def open_api_json_spec(req: Request, res: Response):
    """
    Serves the OpenAPI JSON spec
    """
    return res.json(req.app.openapi_spec).status(200)


async def open_api_swagger(req: Request, res: Response):
    """
    Serves the Swagger UI, pointing to the JSON spec route
    """
    return res.text(f"""
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
                const ui = SwaggerUIBundle({{
                    url: "{req.app.get_conf('OPEN_API_JSON_URL')}",
                    dom_id: '#swagger-ui',
                }})
                </script>
            </body>
        </html>
    """)


# ------------------------------------------------------------------------------
# Main Extension Class for Generating OpenAPI Specs
# ------------------------------------------------------------------------------

class OpenApiExtension:
    """
    Extension class for OpenAPI support.
    Relies on self.openapi_registry, self.app_name, self.version, etc. being set
    elsewhere in your application.
    """

    def generate_openapi_spec(self) -> dict:
        """
        Generates the final OpenAPI schema spec and stores it in self.openapi_spec.
        """
        openapi_spec = {
            "openapi": "3.0.3",
            "info": {"title": self.app_name, "version": self.version},
            "components": {
                "schemas": {}
            },
            "paths": {},
        }

        for method, routes in self.openapi_registry.items():
            for path, meta in routes.items():
                if path not in openapi_spec["paths"]:
                    openapi_spec["paths"][path] = {}

                # Build the method definition (operation)
                path_obj = {
                    "operationId": meta.get("operation_id", ""),
                    "summary": meta.get("summary", ""),
                    "description": meta.get("description", ""),
                    "responses": {
                        str(meta.get('response_code', 200)): {
                            "description": "Success"
                        }
                    }
                }

                # ------------------------------------------------------------
                # 1) Handle RESPONSE SCHEMA (success responses)
                # ------------------------------------------------------------
                response_schema_cls = meta.get("response_schema", None)
                if response_schema_cls is not None:
                    raw_schema = generate_openapi_json_schema(response_schema_cls)
                    final_ref = self._add_schema_to_components(raw_schema, openapi_spec)

                    status_code = str(meta.get("response_code", 200) or 200)
                    path_obj["responses"][status_code] = {
                        "description": "Success",
                        "content": {
                            "application/json": {
                                "schema": final_ref
                            }
                        }
                    }

                # ------------------------------------------------------------
                # 2) Handle EXCEPTION RESPONSES (error schemas/status codes)
                # ------------------------------------------------------------
                exception_responses = meta.get("exception_responses", None)
                if exception_responses is not None:
                    for schema_cls, statuses in exception_responses.items():
                        raw_schema = generate_openapi_json_schema(schema_cls)
                        final_ref = self._add_schema_to_components(raw_schema, openapi_spec)
                        for status in statuses:
                            path_obj["responses"][str(status)] = {
                                "description": "Error",
                                "content": {
                                    "application/json": {
                                        "schema": final_ref
                                    }
                                }
                            }

                # ------------------------------------------------------------
                # 3) Handle REQUEST SCHEMA
                # ------------------------------------------------------------
                request_location: Optional[str] = meta.get("request_location", None)
                request_schema_cls = meta.get("request_schema", None)
                if request_schema_cls is not None and request_location not in ["query", None]:
                    # For body parameters (e.g. JSON)
                    raw_schema = generate_openapi_json_schema(request_schema_cls)
                    final_ref = self._add_schema_to_components(raw_schema, openapi_spec)
                    path_obj["requestBody"] = {
                        "content": {
                            "application/json": {
                                "schema": final_ref
                            }
                        }
                    }

                # If request_location == "query", treat each field as a query parameter
                if request_location == "query" and request_schema_cls is not None:
                    raw_schema = generate_openapi_json_schema(request_schema_cls)
                    self._add_query_schema(path_obj, raw_schema)

                # If no explicit responses have been assigned, ensure "200" is present
                if not path_obj["responses"]:
                    path_obj["responses"]["200"] = {"description": "Success"}

                # Insert the method definition into the path
                openapi_spec["paths"][path][method.lower()] = path_obj

        self.openapi_spec = openapi_spec
        return openapi_spec

    def _add_query_schema(self, route_obj: dict, schema: dict):
        """
        Adds query parameters (in='query') to the route's 'parameters' list
        based on the provided schema dict.
        """
        query_params = self._generate_query_parameters(schema)
        if "parameters" not in route_obj:
            route_obj["parameters"] = []
        route_obj["parameters"].extend(query_params)

    def _generate_query_parameters(self, schema: dict) -> list[dict]:
        """
        Converts a Marshmallow/Pydantic JSON Schema into a list of
        OpenAPI parameters, each marked as in="query".
        """
        # Attempt to see if there's a top-level $ref
        top_ref = schema.get("$ref")  # e.g. "#/definitions/UserQueryInSchema"
        if top_ref and top_ref.startswith("#/definitions/"):
            # Extract the schema name from the ref
            schema_name = top_ref.replace("#/definitions/", "")
            # The real schema is under schema["definitions"][schema_name]
            real_schema = schema["definitions"].get(schema_name, {})
            properties = real_schema.get("properties", {})
            required_fields = real_schema.get("required", [])
        else:
            # If there's no top-level ref, assume 'properties' are directly under the schema
            properties = schema.get("properties", {})
            required_fields = schema.get("required", [])

        parameters = []
        for field_name, field_info in properties.items():
            # The JSON schema "type" might be "string", "integer", etc.
            # Default to "string" if not explicitly provided.
            param_type = field_info.get("type", "string")

            param_def = {
                "name": field_name,
                "in": "query",
                "required": field_name in required_fields,
                "schema": {
                    "type": param_type
                }
            }
            parameters.append(param_def)

        return parameters

    def _add_schema_to_components(self, schema_dict: dict, openapi_spec: dict) -> dict:
        """
        Takes a JSON Schema dict (from Marshmallow or Pydantic) and the main
        openapi_spec dictionary. Moves 'definitions' into openapi_spec["components"]["schemas"].
        
        Then, if there's a top-level $ref referencing '#/definitions/...', it rewrites it to
        '#/components/schemas/<Name>'. Otherwise, if there's a schema 'title', we store the
        entire schema under that title in '#/components/schemas/<title>' and return a ref
        to that component.

        This ensures that Pydantic models (which typically don't have a top-level $ref)
        still appear in the Schemas section.
        """
        if "components" not in openapi_spec:
            openapi_spec["components"] = {}
        if "schemas" not in openapi_spec["components"]:
            openapi_spec["components"]["schemas"] = {}

        # Move nested definitions -> components.schemas
        definitions = schema_dict.pop("definitions", {})
        for schema_name, schema_def in definitions.items():
            openapi_spec["components"]["schemas"][schema_name] = schema_def

        # Check for Marshmallow-style top-level $ref
        ref_str = schema_dict.get("$ref")
        if ref_str and ref_str.startswith("#/definitions/"):
            schema_name = ref_str.replace("#/definitions/", "")
            return {"$ref": f"#/components/schemas/{schema_name}"}

        # If no top-level $ref, store the entire schema in 'components.schemas'
        # under its 'title' (Pydantic models usually include a title).
        title = schema_dict.get("title")
        if title:
            openapi_spec["components"]["schemas"][title] = schema_dict
            return {"$ref": f"#/components/schemas/{title}"}

        # If there's no title, just return as-is (final fallback).
        return schema_dict


    def _merge_openapi_registry(self, bp: Blueprint):
        """
        Merges a Blueprint's openapi_registry object with the application's,
        so that all routes are included in the final OpenAPI spec.
        """
        for method in bp.openapi_registry:
            if method not in self.openapi_registry:
                self.openapi_registry[method] = {}
            for path, handler in bp.openapi_registry[method].items():
                self.openapi_registry[method][path] = handler

