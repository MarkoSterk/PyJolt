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
    BASE_PATH: str = Field(description="Base path of app. os.path.dirname(__file__) in the configs.py is the usual value.")

    # required for Authentication extension
    SECRET_KEY: Optional[str] = Field(None, description="High entropy random string for signing cookies/jwts")

    # optionals with sensible defaults
    DEBUG: Optional[bool] = Field(True, description="If the app should run in debug mode or not.")
    HOST: Optional[str] = Field("localhost", description="Host ip where the app should run.")
    TEMPLATES_DIR: Optional[str] = Field("/templates", description="Relative templates dir from root")
    STATIC_DIR: Optional[str] = Field("/static", description="Relative static dir from root")
    STATIC_URL: Optional[str] = Field("/static", description="URL prefix for static files")
    TEMPLATES_STRICT: Optional[bool] = Field(True, description="Strict template rendering")
    STRICT_SLASHES: Optional[bool] = Field(False, description="Route '/x' vs '/x/' strictness")
    OPEN_API: Optional[bool] = Field(True, description="Enable OpenAPI endpoint")
    OPEN_API_URL: Optional[str] = Field("/openapi", description="OpenAPI base path")
    OPEN_API_DESCRIPTION: Optional[str] = Field("Simple API", description="OpenAPI description")

    # controllers, extensions, models
    CONTROLLERS: Optional[List[str]] = None
    EXTENSIONS: Optional[List[str]] = None
    MODELS: Optional[List[str]] = None

    model_config = ConfigDict(extra="allow")

    @field_validator("CONTROLLERS", "EXTENSIONS", "MODELS", mode="before")
    @classmethod
    def _coerce_list_of_str(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if not isinstance(v, list) or any(not isinstance(x, str) for x in v):
            raise TypeError("Must be a list[str] or None.")
        return v

    @field_validator("CONTROLLERS", "EXTENSIONS", "MODELS")
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
