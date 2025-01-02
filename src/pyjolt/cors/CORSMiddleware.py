"""
CORSMiddleware.py
Cross origin resource sharing middleware
"""
from typing import Callable
from ..pyjolt import PyJolt


async def parse_headers(scope):
    """
    Parse and return headers as a dictionary for easier access.
    """
    return {key.decode("utf-8"): value.decode("utf-8") for key, value in scope["headers"]}

async def validate_origin(origin, allowed_origins, send):
    """
    Validate request origin.
    """
    if allowed_origins != ["*"] and (not origin or origin not in allowed_origins):
        # Blocks the request for invalid origin
        await send({
            "type": "http.response.start",
            "status": 403,
            "headers": [(b"content-type", b"application/json")],
        })
        await send({
            "type": "http.response.body",
            "body": b'{"message": "Forbidden: Origin not allowed", "status": "error"}',
        })
        return False
    return True

async def validate_headers(headers, allowed_headers, send):
    """
    Validate request headers.
    """
    requested_headers = headers.get("access-control-request-headers", "").split(", ")
    invalid_headers = [h for h in requested_headers if h not in allowed_headers]
    if invalid_headers:
        #Blocks request with disallowed headers
        await send({
            "type": "http.response.start",
            "status": 403,
            "headers": [(b"content-type", b"application/json")],
        })
        await send({
            "type": "http.response.body",
            "body": b'{"message": "Forbidden: Headers not allowed", "status": "error"}',
        })
        return False
    return True

async def validate_method(method, allowed_methods, send):
    """
    Validate request method.
    """
    if method not in allowed_methods:
        #Block request with disallowed method
        await send({
            "type": "http.response.start",
            "status": 405,
            "headers": [(b"content-type", b"application/json")],
        })
        await send({
            "type": "http.response.body",
            "body": b'{"message": "Method Not Allowed", "status": "error"}',
        })
        return False
    return True

# pylint: disable-next=C0103
def CORSMiddleware(app: PyJolt, app_function: Callable):
    """
    Middleware factory for handling Cross-Origin Resource Sharing (CORS).
    """

    ## Gets configs from application or uses defaults
    allowed_origins = app.get_conf("CORS_ALLOWED_ORIGINS", ["*"])

    allowed_methods = app.get_conf("CORS_ALLOWED_METHODS", ["GET", "POST", "PUT",
                                                            "PATCH", "DELETE", "OPTIONS"])
    #Adds OPTIONS method for preflight checking
    if "OPTIONS" not in allowed_methods:
        allowed_methods.append("OPTIONS")

    allowed_headers = app.get_conf("CORS_ALLOWED_HEADERS", ["Authentication",
                                                            "Authorization",
                                                            "Content-Type"])

    async def middleware(scope, receive, send):
        if scope["type"] != "http":
            # Passes non-HTTP requests to the next layer
            await app_function(scope, receive, send)
            return

        headers = await parse_headers(scope)
        origin = headers.get("origin", None)
        method = scope["method"].upper()

        if not await validate_origin(origin, allowed_origins, send):
            return

        if not await validate_method(method, allowed_methods, send):
            return

        if method == "OPTIONS" and not await validate_headers(headers, allowed_headers, send):
            return

        # Intercepts response sending by wrapping the original send
        async def wrapped_send(event):
            if event["type"] == "http.response.start":
                headers = event.get("headers", [])
                headers.extend([
                    (b"access-control-allow-origin", b", ".join(origin.encode("utf-8") for origin in allowed_origins)),
                    (b"access-control-allow-methods", b", ".join(method.encode("utf-8") for method in allowed_methods)),
                    (b"access-control-allow-headers", b", ".join(header.encode("utf-8") for header in allowed_headers)),
                ])
                event["headers"] = headers
            await send(event)

        # For all other requests, pass to the next layer
        await app_function(scope, receive, wrapped_send)

    return middleware
