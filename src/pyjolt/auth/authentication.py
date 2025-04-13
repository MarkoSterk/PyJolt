"""
authentication.py
Authentication module of PyJolt
"""
from typing import Callable, Optional, Dict
from functools import wraps
import base64
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from cryptography.hazmat.primitives.hmac import HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature

from ..pyjolt import PyJolt
from ..request import Request
from ..response import Response
from ..exceptions import AuthenticationException, InvalidJWTError
from ..utilities import run_sync_or_async

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
                                  "method with the @user_loader or @user_loader_middleware decorator before using "
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
        self._user_loader_middleware: Callable = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app: PyJolt):
        """
        Configures authentication module
        """
        self._app = app
        self.unauthorized_message = app.get_conf("UNAUTHORIZED_MESSAGE",
                                                 self.DEFAULT_UNAUTHORIZED_MESSAGE)
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
        except (ValueError, IndexError, base64.binascii.Error, InvalidSignature):
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
    
    def create_jwt_token(self, payload: Dict, expires_in: Optional[int] = 3600) -> str:
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

    def validate_jwt_token(self, token: str) -> Dict:
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
    
    def middleware(self, app: PyJolt, app_function: Callable):
        """
        Parses incoming request for user information
        """

        #return await app(scope, receive, send)
        async def auth_middleware(req, res, send):
            if req.scope["type"] != "http":
                # Passes non-HTTP requests to the next layer
                return await run_sync_or_async(app_function, req, res, send)

            user: any = None
            if req.scope["type"] == "http":
                headers = headers = {k.decode().lower(): v.decode() for k, v in req.scope["headers"]}
                if self._user_loader_middleware is None:
                    raise ValueError(self.USER_LOADER_ERROR_MSG)
                user = await run_sync_or_async(self._user_loader_middleware, headers)
            
            # Store the user ID in the scope for downstream middleware
            req.set_user(user)

            # Intercepts response sending by wrapping the original send
            async def wrapped_send(event):
                await send(event)

            # For all other requests, pass to the next layer
            return await run_sync_or_async(app_function, req, res, wrapped_send)

        return auth_middleware

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
                #If the authentication middleware was used
                #the req.user object is already loaded and the
                #if-clause is skipped. Else, the app tries to
                #load the user with the user_loader method provided by the
                #user_loader decorator.
                if req.user is None:
                    if self._user_loader is None:
                        raise ValueError(self.USER_LOADER_ERROR_MSG)
                    req.set_user(await self._user_loader(req))
                if req.user is None:
                    raise AuthenticationException(self.unauthorized_message)
                return await handler(*args, *kwargs)
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

    @property
    def user_loader_middleware(self):
        """
        Decorator for designating a user loader method from the received
        headers (dictionary). The method should return the user object (db model, 
        dictionary or any other type) or None
        """
        def decorator(func: Callable):
            self._user_loader_middleware = func
            return func
        return decorator
