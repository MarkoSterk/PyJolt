"""
Response class. Holds all information regarding responses to individual requests
"""
import json

from .exceptions import Jinja2NotInitilized

class Response:
    """Holds status_code, headers, and body to be sent back."""
    def __init__(self, render_engine):
        self.status_code = 200
        self.headers = {}
        self.body = b""
        self.render_engine = render_engine

    def status(self, status_code: int):
        """
        Sets status code of response
        """
        self.status_code = status_code
        return self

    def json(self, data, status_code=200):
        """
        Stringifies json data and creates json response
        with application/json content-type and default
        status code 200
        """
        self.status_code = status_code
        self.headers["content-type"] = "application/json"
        self.body = json.dumps(data).encode()
        return self

    def html(self, template_path: str, context: dict[str, any] = None, status_code=200):
        """
        Renders html template and creates response with text/html content-type
        and default status code 200

        template_path: relative path of template inside the templates folder
        context: dictionary with data used in the template
        """
        if self.render_engine is None:
            raise Jinja2NotInitilized()

        if context is None:
            context = {}

        template = self.render_engine.get_template(template_path)
        rendered = template.render(**context)
        self.status_code = status_code
        self.headers["content-type"] = "text/html"
        self.body = rendered.encode("utf-8")
        return self

    def send_file(self, body, status_code, headers):
        """
        For sending files
        Sets correct headers and body of the response
        """
        self.status_code = status_code
        for k, v in headers.items():
            self.headers[k] = v
        self.body = body
        return self
    
    def set_header(self, key: str, value: str):
        """
        Sets or updates a header in the response.

        key: Header name
        value: Header value
        """
        self.headers[key.lower()] = value
        return self

    def set_cookie(self, cookie_name: str, value: str,
                   max_age: int = None, path: str = "/",
                   domain: str = None, secure: bool = False,
                   http_only: bool = True):
        """
        Sets a cookie in the response.

        cookie_name: Cookie name
        value: Cookie value
        max_age: Max age of the cookie in seconds (optional)
        path: Path where the cookie is available (default "/")
        domain: Domain where the cookie is available (optional)
        secure: If True, the cookie is only sent over HTTPS (default False)
        http_only: If True, the cookie is inaccessible to JavaScript (default True) <-- MORE SECURE
        """
        cookie_parts = [f"{cookie_name}={value}"]

        if max_age is not None:
            cookie_parts.append(f"Max-Age={max_age}")
        if path:
            cookie_parts.append(f"Path={path}")
        if domain:
            cookie_parts.append(f"Domain={domain}")
        if secure:
            cookie_parts.append("Secure")
        if http_only:
            cookie_parts.append("HttpOnly")

        cookie_header = "; ".join(cookie_parts)
        if "set-cookie" in self.headers:
            self.headers["set-cookie"] += f", {cookie_header}"
        else:
            self.headers["set-cookie"] = cookie_header

        return self
    
    def delete_cookie(self, cookie_name: str, path: str = "/", domain: str = None):
        """
        Deletes a cookie by setting its Max-Age to 0.

        cookie_name: Cookie name
        path: Path where the cookie was available (default "/")
        domain: Domain where the cookie was available (optional)
        """
        cookie_parts = [f"{cookie_name}=", "Max-Age=0", f"Path={path}"]

        if domain:
            cookie_parts.append(f"Domain={domain}")

        cookie_header = "; ".join(cookie_parts)
        if "set-cookie" in self.headers:
            self.headers["set-cookie"] += f", {cookie_header}"
        else:
            self.headers["set-cookie"] = cookie_header

        return self
