"""
Vendor Pydantic schemas.

Defines request/response shapes for vendor CRUD endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class VendorBase(BaseModel):
    """Fields shared across vendor schemas."""

    company_name: str = Field(..., min_length=1, max_length=512, description="Legal company name")
    contact_person: str | None = Field(None, max_length=256, description="Primary contact name")
    email: EmailStr | None = Field(None, description="Contact email")
    phone: str | None = Field(None, max_length=50, description="Contact phone number")
    website: str | None = Field(None, max_length=512, description="Website URL")
    address: str | None = Field(None, max_length=2048, description="Full postal address")
    country: str | None = Field(None, max_length=100, description="Country of operation")
    tax_number: str | None = Field(None, max_length=100, description="GST / Tax ID number")
    notes: str | None = Field(None, max_length=4096, description="Internal notes")
    is_active: bool = Field(True, description="Whether the vendor is active")


class VendorCreate(VendorBase):
    """Payload for creating a new vendor."""
    pass


class VendorUpdate(BaseModel):
    """Partial update schema — all fields optional."""

    company_name: str | None = Field(None, min_length=1, max_length=512)
    contact_person: str | None = None
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    website: str | None = Field(None, max_length=512)
    address: str | None = Field(None, max_length=2048)
    country: str | None = Field(None, max_length=100)
    tax_number: str | None = Field(None, max_length=100)
    notes: str | None = Field(None, max_length=4096)
    is_active: bool | None = None


class VendorResponse(VendorBase):
    """Public vendor representation returned by the API."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PaginatedVendorResponse(BaseModel):
    """Envelope for paginated vendor list responses."""

    items: list[VendorResponse]
    total: int
    page: int
    page_size: int
    pages: int
