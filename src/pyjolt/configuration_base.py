"""
Base configuration class
"""

from __future__ import annotations

import re
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator

IMPORT_STR_RE = re.compile(r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*:[A-Za-z_]\w*$")


class BaseConfig(BaseModel):
    # required
    APP_NAME: str = Field(description="Human-readable name of the app")
    VERSION: str = Field(description="Application version")
    BASE_PATH: str = Field(
        description="Base path of app. os.path.dirname(__file__) in the configs.py is the usual value."
    )

    # required for Authentication extension
    SECRET_KEY: Optional[str] = Field(
        None, description="High entropy random string for signing cookies/jwts"
    )

    # optionals with sensible defaults
    DEBUG: Optional[bool] = Field(
        True, description="If the app should run in debug mode or not."
    )
    HOST: Optional[str] = Field(
        "localhost", description="Host ip where the app should run."
    )
    PORT: Optional[int] = Field(8080, description="Port on which the app should run.")
    LIFESPAN: Optional[str] = Field("on", description="Whether to use server lifespan events/signals. Options: on, auto, off")
    TEMPLATES_DIR: Optional[str] = Field(
        "/templates", description="Relative templates dir from root"
    )
    STATIC_DIR: Optional[str] = Field(
        "/static", description="Relative static dir from root"
    )
    STATIC_URL: Optional[str] = Field(
        "/static", description="URL prefix for static files"
    )
    TEMPLATES_STRICT: Optional[bool] = Field(
        True, description="Strict template rendering"
    )
    STRICT_SLASHES: Optional[bool] = Field(
        False, description="Route '/x' vs '/x/' strictness"
    )
    OPEN_API: Optional[bool] = Field(True, description="Enable OpenAPI endpoint")
    OPEN_API_URL: Optional[str] = Field("/openapi", description="OpenAPI base path")
    OPEN_API_DESCRIPTION: Optional[str] = Field(
        "Simple API", description="OpenAPI description"
    )

    #CORS settings
    CORS_ENABLED: Optional[bool] = Field(True, description="Enable CORS")
    CORS_ALLOW_ORIGINS: Optional[list[str]] = Field(["*"], description="List of allowed origins")
    CORS_ALLOW_METHODS: Optional[list[str]] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: Optional[list[str]] = Field(["Authorization", "Content-Type"], description="List of allowed headers")
    CORS_EXPOSE_HEADERS: Optional[list[str]] = Field([], description="Expose headers")
    CORS_ALLOW_CREDENTIALS: Optional[bool] = Field(True, description="Allow credentials")
    CORS_MAX_AGE: Optional[int] = Field(None, description="Max age in seconds. None to disable.")

    # controllers, extensions, models
    CONTROLLERS: Optional[List[str]] = None
    CLI_CONTROLLERS: Optional[List[str]] = None
    EXTENSIONS: Optional[List[str]] = None
    MODELS: Optional[List[str]] = None
    EXCEPTION_HANDLERS: Optional[List[str]] = None

    model_config = ConfigDict(extra="allow")

    @field_validator("CONTROLLERS", "EXTENSIONS", "MODELS", "EXCEPTION_HANDLERS", mode="before")
    @classmethod
    def _coerce_list_of_str(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if not isinstance(v, list) or any(not isinstance(x, str) for x in v):
            raise TypeError("Must be a list[str] or None.")
        return v

    @field_validator("CONTROLLERS", "EXTENSIONS", "MODELS", "EXCEPTION_HANDLERS")
    @classmethod
    def _validate_import_strings(cls, v):
        if not v:
            return v
        bad = [s for s in v if not IMPORT_STR_RE.match(s)]
        if bad:
            raise ValueError(
                "Invalid import strings (use 'package.module:ClassOrObject'): "
                + ", ".join(bad)
            )
        return v
    
    @staticmethod
    def value_to_bool(value: str|int|bool) -> bool:
        """
        Turns a boolean-like value to boolean.

        :param str value: a string value representing a boolean

        Returns True if value in [True, "true", "True", "1", 1]
        """
        return value in [True, "true", "True", "1", 1]
