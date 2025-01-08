"""
OpenAPI/Swagger interface
"""
from .pyjolt import Request, Response

async def open_api_json_spec(req: Request, res: Response):
    """
    Serves OpenAPI json spec
    """
    res.json(req.app.open_api_json_spec).status(200)

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
