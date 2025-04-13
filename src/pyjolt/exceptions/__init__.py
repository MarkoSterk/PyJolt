"""
Exceptions submodule
"""

from .http_exceptions import (BaseHttpException,
                            StaticAssetNotFound,
                            AborterException,
                            MissingRequestData,
                            SchemaValidationError,
                            PydanticSchemaValidationError,
                            AuthenticationException,
                            InvalidJWTError,
                            abort)

from .runtime_exceptions import (DuplicateRoutePath,
                                DuplicateExceptionHandler,
                                Jinja2NotInitilized,
                                MissingExtension,
                                MissingDependencyInjectionMethod,
                                MissingResponseObject,
                                MissingRouterInstance,
                                InvalidRouteHandler,
                                InvalidWebsocketHandler)


__all__ = ['BaseHttpException',
            'StaticAssetNotFound',
            'AborterException',
            'MissingRequestData',
            'SchemaValidationError',
            'PydanticSchemaValidationError',
            'AuthenticationException',
            "InvalidJWTError",
            'abort',
            'DuplicateRoutePath',
            'DuplicateExceptionHandler',
            'Jinja2NotInitilized',
            'MissingExtension',
            'MissingDependencyInjectionMethod',
            'MissingResponseObject',
            'MissingRouterInstance',
            'InvalidRouteHandler',
            'InvalidWebsocketHandler']
