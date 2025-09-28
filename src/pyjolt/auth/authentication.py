"""
authentication.py
Authentication module of PyJolt
"""
from abc import ABC, abstractmethod
from typing import Callable, Optional, Dict, Any, TYPE_CHECKING, cast
from functools import wraps
import base64
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import binascii
from cryptography.hazmat.primitives.hmac import HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature

from ..exceptions import AuthenticationException, UnauthorizedException
from ..utilities import run_sync_or_async
from ..request import Request
from ..base_extension import BaseExtension
if TYPE_CHECKING:
    from ..pyjolt import PyJolt
    from ..response import Response
    from ..controller import Controller

class Authentication(BaseExtension, ABC):
    """
    Authentication class for PyJolt
    """

    REQUEST_ARGS_ERROR_MSG: str = ("Injected argument 'req' of route handler is not an instance "
                    "of the Request class. If you used additional decorators "
                    "make sure the order of arguments was not changed. "
                    "The Request argument must always come first.")
    
    USER_LOADER_ERROR_MSG: str = ("Undefined user loader method. Please define a user loader "
                                  "method with the @user_loader decorator before using "
                                  "the login_required decorator")

    _DEFAULT_CONFIGS = {
        "DEFAULT_AUTHENTICATION_ERROR_MESSAGE": "Login required",
        "DEFAULT_AUTHORIZATION_ERROR_MESSAGE": "Missing user role(s)"
    }

    def __init__(self, variable_prefix: str = "") -> None:
        """
        Initilizer for authentication module
        """
        self._app: "Optional[PyJolt]" = None
        self._variable_prefix: str = variable_prefix

    def init_app(self, app: "PyJolt"):
        """
        Configures authentication module
        """
        self._app = app
        self.authentication_error = app.get_conf(f"{self._variable_prefix}AUTHENTICATION_ERROR_MESSAGE",
                                                 self._DEFAULT_CONFIGS["DEFAULT_AUTHENTICATION_ERROR_MESSAGE"])
        self.authorization_error = app.get_conf(f"{self._variable_prefix}UNAUTHORIZED_ERROR_MESSAGE",
                                                 self._DEFAULT_CONFIGS["DEFAULT_AUTHORIZATION_ERROR_MESSAGE"])
        self._app.add_extension(self)

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
        except (ValueError, IndexError, binascii.Error, InvalidSignature):
            # pylint: disable-next=W0707
            raise ValueError("Invalid signed cookie format or signature.")

    def create_password_hash(self, password: str) -> str:
        """
        Creates a secure hash for a given password.

        password: The plain text password to be hashed
        Returns the hashed password as a string.
        """
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    def check_password_hash(self, password: str, hashed_password: str) -> bool:
        """
        Verifies a given password against a hashed password.

        password: The plain text password provided by the user
        hashed_password: The stored hashed password
        Returns True if the password matches, False otherwise.
        """
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    
    def create_jwt_token(self, payload: Dict, expires_in: int = 3600) -> str:
        """
        Creates a JWT token.

        :param payload: A dictionary containing the payload data.
        :param expires_in: Token expiry time in seconds (default: 3600 seconds = 1 hour).
        :return: Encoded JWT token as a string.
        """
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a dictionary.")

        # Add expiry to the payload
        payload = payload.copy()
        payload["exp"] = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # Create the token using the app's SECRET_KEY
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        return token

    def validate_jwt_token(self, token: str) -> Dict|None:
        """
        Validates a JWT token.

        :param token: The JWT token to validate.
        :return: Decoded payload if the token is valid.
        :raises: InvalidJWTError if the token is expired.
                 InvalidJWTError for other validation issues.
        """
        try:
            # Decode the token using the app's SECRET_KEY
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
    
    @property
    def secret_key(self):
        """
        Returns app secret key or none
        """
        sec_key = self._app.get_conf("SECRET_KEY", None)
        if sec_key is None:
            raise ValueError("SECRET_KEY is not defined in app configurations")
        return sec_key

    @property
    def login_required(self) -> Callable[[Callable], Callable]:
        """
        Decorator enforcing that a user is authenticated before the endpoint runs.

        Usage:
            @auth.login_required
            async def endpoint(self, req: Request, ...): ...
        """
        authenticator = self

        def decorator(handler: Callable) -> Callable:
            @wraps(handler)
            async def wrapper(self: "Controller", *args, **kwargs) -> "Response":
                if not args:
                    raise RuntimeError(
                        "Request must be auto-injected as the first argument after self."
                    )
                req: "Request" = args[0]
                if not isinstance(req, Request):
                    raise ValueError(authenticator.REQUEST_ARGS_ERROR_MSG)
                if req.user is None:
                    user_loader = getattr(authenticator, "user_loader", None)
                    if user_loader is None:
                        raise ValueError(authenticator.USER_LOADER_ERROR_MSG)
                    req.set_user(await run_sync_or_async(user_loader, req))
                if req.user is None:
                    # Not authenticated
                    raise AuthenticationException(authenticator.authentication_error)

                return await run_sync_or_async(handler, self, *args, **kwargs)

            return wrapper

        return decorator
    

    def role_required(self, *roles) -> Callable[[Callable], Callable]:
        """
        Decorator enforcing that a user has designated roles.
        Decorator must be BELOW the login_required decorator
        Usage:
            @auth.role_required(*roles)
            async def endpoint(self, req: Request, ...): ...
        """
        authenticator = self

        def decorator(handler: Callable) -> Callable:
            @wraps(handler)
            async def wrapper(self: "Controller", *args, **kwargs) -> "Response":
                if not args:
                    raise RuntimeError(
                        "Request must be auto-injected as the first argument after self."
                    )
                req: "Request" = args[0]
                if not isinstance(req, Request):
                    raise ValueError(authenticator.REQUEST_ARGS_ERROR_MSG)

                if req.user is None:
                    raise RuntimeError(
                        "User not loaded. Make sure the method is decorated with @login_required to load the user object"
                    )
                authorized: bool = await run_sync_or_async(authenticator.role_check, req.user, list(roles))
                if not authorized:
                    #not authorized
                    raise UnauthorizedException(authenticator.authorization_error, list(roles))

                return await run_sync_or_async(handler, self, *args, **kwargs)

            return wrapper

        return decorator

    @abstractmethod
    async def user_loader(self, req: "Request") -> Any:
        """
        Should return a user object (or None) loaded from the cookie
        or some other way provided by the request object
        """

    @abstractmethod
    async def role_check(self, user: Any, roles: list[Any]) -> bool:
        """
        Should check if user has required role(s) and return a boolean
        True -> user has role(s)
        False -> user doesn't have role(s)
        """
