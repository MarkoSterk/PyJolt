"""
OpenAPI controller
"""
from pydantic import BaseModel
from typing import Any

from .http_statuses import HttpStatus
from .media_types import MediaType
from .response import Response
from .request import Request
from .controller import Controller, get, produces

class OpenApiSpecs(BaseModel):

    openapi: str = "3.0.3"
    info: Any = None
    servers: Any = None
    paths: Any = None
    components: Any = None

class OpenAPI(Controller):

    @get("/specs.json")
    @produces(MediaType.APPLICATION_JSON)
    async def specs(self, req: Request) -> Response[OpenApiSpecs]:
        return req.response.json(self.app.json_spec).status(HttpStatus.OK)

    @get("/docs")
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
                        url: "{{ url_for('OpenAPI.specs') }}",
                        dom_id: '#swagger-ui',
                    })
                </script>
            </body>
        </html>
        """)).status(HttpStatus.OK)
