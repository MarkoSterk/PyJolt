"""
OpenAPI/Swagger interface
"""
from marshmallow_jsonschema import JSONSchema
from .pyjolt import Request, Response, Blueprint

async def open_api_json_spec(req: Request, res: Response):
    """
    Serves OpenAPI json spec
    """
    res.json(req.app.openapi_spec).status(200)

async def open_api_swagger(req: Request, res: Response):
    """
    Serves OpenAPI Swagger UI
    """
    res.text(f"""
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

class OpenApiExtension:
    """
    Extension class for OpenAPI support
    """

    def generate_openapi_spec(self) -> dict:
        """
        Generates final openapi schema spec
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

                # Method definition
                path_obj = {
                    "operationId": meta.get("operation_id", ""),
                    "summary": meta.get("summary", ""),
                    "description": meta.get("description", ""),
                    "responses": {
                        f"{meta.get('response_code', 200)}": {
                            "description": "Success"
                        }
                    }
                }
                response_schema_cls = meta.get("response_schema", None)  # Marshmallow class
                if response_schema_cls is not None:
                    raw_schema = JSONSchema().dump(response_schema_cls())

                    # Move definitions into components, get an OAS-compatible $ref
                    final_ref = self._add_marshmallow_schema_to_components(raw_schema, openapi_spec)

                    status_code = meta.get("response_code", 200) or 200
                    code_str = str(status_code)

                    path_obj["responses"][code_str] = {
                        "description": "Success",
                        "content": {
                            f"{meta.get("request_location")}": {
                                "schema": final_ref
                            }
                        }
                    }
                request_location: str = meta.get("request_location", None)
                request_schema_cls = meta.get("request_schema", None)  # Marshmallow class
                if request_schema_cls is not None and request_location not in ["query", None]:
                    raw_schema = JSONSchema().dump(request_schema_cls())
                    final_ref = self._add_marshmallow_schema_to_components(raw_schema, openapi_spec)

                    path_obj["requestBody"] = {
                        "content": {
                            "application/json": {
                                "schema": final_ref
                            }
                        }
                    }
                if request_location == "query" and request_schema_cls is not None:
                    raw_schema = JSONSchema().dump(request_schema_cls())
                    self._add_query_schema(path_obj, raw_schema)

                if not path_obj["responses"]:
                    path_obj["responses"]["200"] = {"description": "Success"}
                openapi_spec["paths"][path][method.lower()] = path_obj
        self.openapi_spec = openapi_spec

    def _add_query_schema(self, route_obj, schema: dict):
        """
        Adds query schema
        """
        query_params = self._generate_query_parameters(schema)
        # Merges them into the route_obj's "parameters" list
        if "parameters" not in route_obj:
            route_obj["parameters"] = []
        route_obj["parameters"].extend(query_params)

    def _generate_query_parameters(self, schema: dict) -> list[dict]:
        """
        Converts a Marshmallow schema into a list of OpenAPI parameters,
        each marked as in="query".
        """
        # 2) Extract the properties and required fields
        top_ref = schema.get("$ref")  # e.g. "#/definitions/UserQueryInSchema"
        if top_ref and top_ref.startswith("#/definitions/"):
            # Extract the schema name from the ref
            schema_name = top_ref.replace("#/definitions/", "")
            # The real schema is under schema["definitions"][schema_name]
            real_schema = schema["definitions"][schema_name]
            properties = real_schema.get("properties", {})
            required_fields = real_schema.get("required", [])
        else:
            # Fallback: if there's no top-level ref, assume
            # properties are directly under schema
            properties = schema.get("properties", {})
            required_fields = schema.get("required", [])

        # 3) Build an OpenAPI parameter for each property
        parameters = []
        for field_name, field_info in properties.items():
            # The JSON schema "type" might be "string", "integer", etc.
            # If not present, default to "string" to keep it safe.
            param_type = field_info.get("type", "string")

            param = {
                "name": field_name,
                "in": "query",
                "required": field_name in required_fields,
                "schema": {
                    "type": param_type
                }
            }

            parameters.append(param)

        return parameters

    def _add_marshmallow_schema_to_components(self, schema: dict, openapi_spec: dict) -> dict:
        """
        Takes a single Marshmallow-generated schema dict (schema) and the main 
        openapi_spec dictionary. Moves the 'definitions' into openapi_spec["components"]["schemas"], 
        then returns a new dict with '$ref' pointing to '#/components/schemas/SchemaName'.
        """

        # 1) Ensure 'components.schemas' exists
        if "components" not in openapi_spec:
            openapi_spec["components"] = {}
        if "schemas" not in openapi_spec["components"]:
            openapi_spec["components"]["schemas"] = {}

        # 2) Extract definitions from schema
        definitions = schema.pop("definitions", {})
        # e.g. definitions might look like: {"MyMarshSchemaName": {...}, "NestedSchema": {...}}

        # 3) Insert each definition into openapi_spec["components"]["schemas"]
        for schema_name, schema_def in definitions.items():
            openapi_spec["components"]["schemas"][schema_name] = schema_def

        # 4) Grab the top-level $ref (if present)
        ref_str = schema.get("$ref")  # e.g. "#/definitions/MyMarshSchemaName"
        if ref_str and ref_str.startswith("#/definitions/"):
            # Extract the name from "#/definitions/MyMarshSchemaName"
            schema_name = ref_str.replace("#/definitions/", "")
            # 5) Return a new dict with a reference to #/components/schemas/<SchemaName>
            return {"$ref": f"#/components/schemas/{schema_name}"}
        else:
            return schema
    
    def _merge_openapi_registry(self, bp: Blueprint):
        """
        Merges blueprints openapi_registry object with the applications
        """
        for method in bp.openapi_registry:
            if method not in self.openapi_registry:
                self.openapi_registry[method] = {}
            for path, handler in bp.openapi_registry[method].items():
                self.openapi_registry[method][path] = handler
