"""
Quotation Pydantic schemas.

Defines request/response shapes for quotation CRUD and file upload endpoints.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.quotation import QuotationStatus


class QuotationBase(BaseModel):
    """Fields shared across quotation schemas."""

    quotation_number: str = Field(
        ..., min_length=1, max_length=128, description="Vendor-assigned reference number"
    )
    quotation_date: str | None = Field(
        None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date on the document (YYYY-MM-DD)"
    )
    currency: str = Field(
        default="USD", max_length=10, description="ISO 4217 currency code"
    )
    total_amount: Decimal | None = Field(
        None, ge=0, decimal_places=2, description="Total quoted amount"
    )


class QuotationCreate(QuotationBase):
    """Payload for creating a quotation record (file uploaded separately)."""

    vendor_id: uuid.UUID = Field(..., description="Vendor who submitted this quotation")
    status: QuotationStatus = Field(
        default=QuotationStatus.PENDING, description="Initial status"
    )


class QuotationUpdate(BaseModel):
    """Partial update schema — all fields optional."""

    quotation_number: str | None = Field(None, min_length=1, max_length=128)
    quotation_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    currency: str | None = Field(None, max_length=10)
    total_amount: Decimal | None = Field(None, ge=0)
    status: QuotationStatus | None = None


class QuotationResponse(QuotationBase):
    """Full quotation representation returned by the API."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    vendor_id: uuid.UUID
    uploaded_by: uuid.UUID
    status: QuotationStatus
    file_name: str | None
    file_path: str | None
    mime_type: str | None
    file_size: int | None
    created_at: datetime
    updated_at: datetime


class PaginatedQuotationResponse(BaseModel):
    """Envelope for paginated quotation list responses."""

    items: list[QuotationResponse]
    total: int
    page: int
    page_size: int
    pages: int


class UploadResponse(BaseModel):
    """Response returned after a successful file upload."""

    quotation_id: uuid.UUID
    file_name: str
    file_size: int
    mime_type: str
    status: QuotationStatus
    message: str = "File uploaded successfully"
