"""
User response models
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, Field
from .base_schema import BaseResponse

class LoginSchema(BaseModel):
    """Login schema"""
    email: EmailStr
    password: str
    remember: Optional[bool] = Field(False, description="Long duration cookie")

    @field_validator("password")
    @classmethod
    def check_min_length(cls, value):
        """Min length check"""
        min_length = 8  # for example
        if len(value) < min_length:
            raise ValueError(f"Email must be at least {min_length} characters long.")
        return value

class UserRegisterSchema(BaseModel):
    """User registration schema. Used in CLI"""
    email: EmailStr
    fullname: str
    password: str
    confirm_password: str

    @field_validator("password")
    @classmethod
    def check_min_length(cls, value):
        """Min length check"""
        min_length = 8  # for example
        if len(value) < min_length:
            raise ValueError(f"Email must be at least {min_length} characters long.")
        return value

class UserOutSchema(BaseModel):
    """Standard user out model"""
    id: int
    fullname: str
    email: str

class LoginOutSchema(BaseResponse):
    """Schema for successful login"""
    data: UserOutSchema
