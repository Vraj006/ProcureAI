"""
Workspace Pydantic schemas.

Defines the data shapes for workspace creation, updates, and API responses.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class WorkspaceBase(BaseModel):
    """Fields shared by create and response schemas."""

    name: str = Field(..., min_length=1, max_length=256, description="Workspace name")
    description: str | None = Field(None, max_length=2048, description="Optional description")


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class WorkspaceCreate(WorkspaceBase):
    """Payload for creating a new workspace."""
    pass


class WorkspaceUpdate(BaseModel):
    """Schema for updating a workspace. All fields optional."""

    name: str | None = Field(None, min_length=1, max_length=256)
    description: str | None = Field(None, max_length=2048)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class WorkspaceResponse(WorkspaceBase):
    """Public-facing workspace representation."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
