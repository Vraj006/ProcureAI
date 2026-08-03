"""
Auth Pydantic schemas.

Defines request/response shapes for authentication endpoints:
registration, login, and token refresh.
"""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Payload for POST /api/v1/auth/register."""

    email: EmailStr = Field(..., description="Email address")
    full_name: str = Field(..., min_length=1, max_length=256, description="Display name")
    password: str = Field(..., min_length=8, max_length=128, description="Password")


class LoginRequest(BaseModel):
    """Payload for POST /api/v1/auth/login (JSON body)."""

    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")


class TokenResponse(BaseModel):
    """Response returned after successful authentication or token refresh."""

    access_token: str = Field(..., description="Short-lived JWT access token")
    refresh_token: str = Field(..., description="Long-lived JWT refresh token")
    token_type: str = Field(default="bearer", description="OAuth2 token type")


class RefreshRequest(BaseModel):
    """Payload for POST /api/v1/auth/refresh."""

    refresh_token: str = Field(..., description="Valid refresh token to exchange")
