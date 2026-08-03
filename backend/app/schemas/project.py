"""
Procurement Project Pydantic schemas.

Defines request/response shapes for project CRUD and
the paginated list response envelope.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.project import ProjectStatus


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class ProjectBase(BaseModel):
    """Shared project fields."""

    name: str = Field(..., min_length=1, max_length=512, description="Project title")
    description: str | None = Field(None, max_length=4096, description="Requirement detail")


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ProjectCreate(ProjectBase):
    """Payload for creating a procurement project."""

    status: ProjectStatus = Field(
        default=ProjectStatus.DRAFT, description="Initial lifecycle state"
    )
    metadata: dict[str, Any] | None = Field(None, description="Arbitrary key-value metadata")


class ProjectUpdate(BaseModel):
    """Schema for partial project update. All fields optional."""

    name: str | None = Field(None, min_length=1, max_length=512)
    description: str | None = Field(None, max_length=4096)
    status: ProjectStatus | None = None
    metadata: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ProjectResponse(ProjectBase):
    """Full project representation returned by the API."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    status: ProjectStatus
    metadata: dict[str, Any] | None = Field(None, alias="metadata_")
    workspace_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class PaginatedProjectResponse(BaseModel):
    """Envelope for paginated project list responses."""

    items: list[ProjectResponse]
    total: int = Field(..., description="Total matching projects (ignoring pagination)")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")
