"""Pydantic schemas for Authentication endpoints."""
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """User registration payload."""
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLoginRequest(BaseModel):
    """User login payload."""
    email: EmailStr
    password: str = Field(min_length=1)


class TokenRefreshRequest(BaseModel):
    """Token refresh payload."""
    refresh_token: str


class TokenResponse(BaseModel):
    """Token response payload containing access and refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class UserResponse(BaseModel):
    """Public user profile response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    is_active: bool
