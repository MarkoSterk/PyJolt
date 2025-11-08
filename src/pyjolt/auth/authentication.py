"""
authentication.py
Authentication module of PyJolt
"""
import warnings
import base64
import binascii
import inspect
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Type, cast

import bcrypt
import jwt
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.hmac import HMAC
from pydantic import BaseModel, Field

from ..base_extension import BaseExtension
from ..exceptions import AuthenticationException, UnauthorizedException
from ..http_methods import HttpMethod
from ..request import Request
from ..utilities import run_sync_or_async

if TYPE_CHECKING:
    from ..pyjolt import PyJolt
    from ..response import Response
from ..controller import Controller

warnings.warn("deprecated", DeprecationWarning)

REQUEST_ARGS_ERROR_MSG: str = ("Injected argument 'req' of route handler is not an instance "
                    "of the Request class. If you used additional decorators "
                    "make sure the order of arguments was not changed. "
                    "The Request argument must always come first.")
    
USER_LOADER_ERROR_MSG: str = ("Undefined user loader method. Please define a user loader "
                                "method with the @user_loader decorator before using "
                                "the login_required decorator")

class AuthenticationConfigs(BaseModel):
    """
    Authentication configuration model
    """
    AUTHENTICATION_ERROR_MSG: Optional[str] = Field(
        default="Login required",
        description="Default authentication error message"
    )
    AUTHORIZATION_ERROR_MSG: Optional[str] = Field(
        default="Missing user role(s)",
        description="Default authorization error message"
    )

class Authentication(BaseExtension, ABC):
    """
    Authentication class for PyJolt
    """

    def __init__(self, configs_name: Optional[str] = "AUTHENTICATION") -> None:
        """
        Initilizer for authentication module
        """
        self._app: "Optional[PyJolt]" = None
        self._configs_name: str = cast(str, configs_name)
        self._configs: dict[str, Any] = {}
        self.authentication_error: str
        self.authorization_error: str

    def init_app(self, app: "PyJolt"):
        """
        Configures authentication module
        """
        self._app = app
        self._configs = app.get_conf(self._configs_name, {})
        self._configs = self.validate_configs(self._configs, AuthenticationConfigs)

        self.authentication_error = self._configs["AUTHENTICATION_ERROR_MSG"]
        self.authorization_error = self._configs["AUTHORIZATION_ERROR_MSG"]
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
    
    async def _check_user_and_run_loader(self, req: "Request") -> "Request":
        """
        Helper method to check and load user for a request
        """
        if req.user is None:
            user_loader = getattr(self, "user_loader", None)
            if user_loader is None:
                raise ValueError(USER_LOADER_ERROR_MSG)
            req.set_user(await run_sync_or_async(user_loader, req))
        if req.user is None:
            raise AuthenticationException(self.authentication_error)
        return req
    
    def _check_user_roles(self, *roles) -> Callable:
        async def __check_user_roles(req: "Request") -> "Request":
            """Checks user roles"""
            if req.user is None:
                if req.method == HttpMethod.SOCKET.value:
                    await req.res.send({"type": "websocket.close", "code": 4401, "reason": "User not authenticated"})
                    return cast("Response", None)  # type: ignore
                raise RuntimeError(
                    "User not loaded. Make sure the method is decorated with @login_required to load the user object"
                )
            authorized: bool = await run_sync_or_async(self.role_check, req.user, list(roles))
            if not authorized:
                #not authorized
                raise UnauthorizedException(self.authorization_error, list(roles))
            return req
        return __check_user_roles

    @property
    def login_required(self) -> Callable[[Callable], Callable]:
        """
        Decorator enforcing that a user is authenticated before the endpoint runs.

        Usage:
            @auth.login_required
            async def endpoint(self, req: Request, ...): ...
        """
        authenticator = self

        def decorator(handler: "Callable|Type[Controller]") -> "Callable|Type[Controller]":
            if inspect.isclass(handler) and issubclass(cast(Type[Controller], handler), Controller):
                """Add authentication pre-request hook to controller"""
                controller_methods: list[Callable] = getattr(handler, "_controller_decorator_methods", []) or []
                controller_methods.append(authenticator._check_user_and_run_loader)
                setattr(handler, "_controller_decorator_methods", controller_methods)
                return handler

            @wraps(handler)
            async def wrapper(self: "Controller", *args, **kwargs) -> "Response":
                if not args:
                    raise RuntimeError(
                        "Request must be auto-injected as the first argument after self."
                    )
                req: "Request" = args[0]
                if not isinstance(req, Request):
                    raise ValueError(REQUEST_ARGS_ERROR_MSG)
                if req.user is None:
                    user_loader = getattr(authenticator, "user_loader", None)
                    if user_loader is None:
                        raise ValueError(USER_LOADER_ERROR_MSG)
                    req.set_user(await run_sync_or_async(user_loader, req))
                if req.user is None:
                    # Not authenticated
                    if req.method == HttpMethod.SOCKET.value:
                        await req.res.send({"type": "websocket.close", "code": 4401, "reason": "User not authenticated"})
                        return cast("Response", None)  # type: ignore
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

        def decorator(handler: "Callable|Type[Controller]") -> "Callable|Type[Controller]":

            if inspect.isclass(handler) and issubclass(cast(Type[Controller], handler), Controller):
                """Add authentication pre-request hook to controller"""
                controller_methods: list[Callable] = getattr(handler, "_controller_decorator_methods", []) or []
                controller_methods.append(self._check_user_roles(*roles))
                setattr(handler, "_controller_decorator_methods", controller_methods)
                return handler

            @wraps(handler)
            async def wrapper(self: "Controller", *args, **kwargs) -> "Response":
                if not args:
                    raise RuntimeError(
                        "Request must be auto-injected as the first argument after self."
                    )
                req: "Request" = args[0]
                if not isinstance(req, Request):
                    raise ValueError(REQUEST_ARGS_ERROR_MSG)

                if req.user is None:
                    if req.method == HttpMethod.SOCKET.value:
                        await req.res.send({"type": "websocket.close", "code": 4401, "reason": "User not authenticated"})
                        return cast("Response", None)  # type: ignore
                    raise RuntimeError(
                        "User not loaded. Make sure the method is decorated with @login_required to load the user object"
                    )
                authorized: bool = await run_sync_or_async(authenticator.role_check, req.user, list(roles))
                if not authorized:
                    #not authorized
                    if req.method == HttpMethod.SOCKET.value:
                        await req.res.send({"type": "websocket.close", "code": 4403, "reason": "User not authorized"})
                        return cast("Response", None)  # type: ignore
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
