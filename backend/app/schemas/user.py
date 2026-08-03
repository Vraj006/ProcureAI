"""
User Pydantic schemas.

Defines the data shapes used for user-related API requests and responses.
Passwords are write-only — never returned in responses.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class UserBase(BaseModel):
    """Shared fields common to creation and response schemas."""

    email: EmailStr = Field(..., description="User's email address (login identifier)")
    full_name: str = Field(
        ..., min_length=1, max_length=256, description="User's display name"
    )


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class UserCreate(UserBase):
    """Schema for registering a new user."""

    password: str = Field(
        ..., min_length=8, max_length=128, description="Plain-text password (min 8 chars)"
    )


class UserUpdate(BaseModel):
    """Schema for updating the current user's profile. All fields optional."""

    full_name: str | None = Field(None, min_length=1, max_length=256)
    password: str | None = Field(None, min_length=8, max_length=128)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class UserResponse(UserBase):
    """Public-facing user representation. Never exposes password or internal flags."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
