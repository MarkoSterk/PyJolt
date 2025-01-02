"""
authentication.py
Authentication module of PyJolt
"""
from typing import Callable
from functools import wraps
import base64

from cryptography.hazmat.primitives.hmac import HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature

from ..pyjolt import PyJolt
from ..request import Request
from ..exceptions import AuthenticationException


class Authentication:
    """
    Authentication class for PyJolt
    """

    REQUEST_ARGS_ERROR_MSG: str = ("Injected argument 'req' of route handler is not an instance "
                    "of the Request class. If you used additional decorators "
                    "or middleware handlers make sure the order of arguments "
                    "was not changed. The Request and Response arguments "
                    "must always come first.")
    
    USER_LOADER_ERROR_MSG: str = ("Undefined user loader method. Please define auser loader "
                                  "method with the @user_loader decorator before using "
                                  "the login_required decorator")
    
    DEFAULT_UNAUTHORIZED_MESSAGE: str = "Login required"

    def __init__(self, app: PyJolt = None):
        """
        Initilizer for authentication module
        """
        self.unauthorized_message: str = None
        self._app: PyJolt = None
        self._user_loader = None
        self._cookie_name: str = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app: PyJolt):
        """
        Configures authentication module
        """
        self._app = app
        self.unauthorized_message = app.get_conf("UNAUTHORIZED_MESSAGE",
                                                 self.DEFAULT_UNAUTHORIZED_MESSAGE)

    def create_signed_cookie_value(self, value: str|int) -> str:
        """
        Creates a signed cookie value using HMAC and a secret key.

        value: The string value to be signed
        secret_key: The application's secret key for signing

        Returns a base64-encoded signed value.
        """
        if isinstance(value, int):
            value = f"{value}"

        hmac_instance = HMAC(self.secret_key.encode("utf-8"), hashes.SHA256())
        hmac_instance.update(value.encode("utf-8"))
        signature = hmac_instance.finalize()
        signed_value = f"{value}|{base64.urlsafe_b64encode(signature).decode('utf-8')}"
        return signed_value

    def decode_signed_cookie(self, cookie_value: str) -> str:
        """
        Decodes and verifies a signed cookie value.

        cookie_value: The signed cookie value to be verified and decoded
        secret_key: The application's secret key for verification

        Returns the original string value if the signature is valid.
        Raises a ValueError if the signature is invalid.
        """
        try:
            value, signature = cookie_value.rsplit("|", 1)
            signature_bytes = base64.urlsafe_b64decode(signature)
            hmac_instance = HMAC(self.secret_key.encode("utf-8"), hashes.SHA256())
            hmac_instance.update(value.encode("utf-8"))
            hmac_instance.verify(signature_bytes)  # Throws an exception if invalid
            return value
        except (ValueError, IndexError, base64.binascii.Error, InvalidSignature):
            # pylint: disable-next=W0707
            raise ValueError("Invalid signed cookie format or signature.")

    @property
    def secret_key(self):
        """
        Returns app secret key or none
        """
        sec_key: str = self._app.get_conf("SECRET_KEY", None)
        if sec_key is None:
            raise ValueError("SECRET_KEY is not defined in app configurations")
        return sec_key

    @property
    def login_required(self) -> Callable:
        """
        Returns a decorator that checks if a user is authenticated
        """
        def decorator(handler: Callable) -> Callable:
            @wraps(handler)
            async def wrapper(*args, **kwargs):
                req: Request = args[0]
                if not isinstance(req, Request):
                    raise ValueError(self.REQUEST_ARGS_ERROR_MSG)
                if self._user_loader is None:
                    raise ValueError(self.USER_LOADER_ERROR_MSG)
                await req.set_user(await self._user_loader(self, req))
                if req.user is None:
                    raise AuthenticationException(self.unauthorized_message)
                await handler(*args, *kwargs)
            return wrapper
        return decorator

    @property
    def user_loader(self):
        """
        Decorator for designating user loader method. The decorated method should return
        the user object (db model, dictionary or any other type) or None in the event of
        unauthorized user.
        """
        def decorator(func: Callable):
            self._user_loader = func
            return func
        return decorator
