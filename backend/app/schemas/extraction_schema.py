"""
Pydantic schemas for structured procurement extraction.

All fields are Optional, defaulting to None, so the LLM may return null
for anything not explicitly present in the source document.
"""

import re
from typing import Optional, Any
import uuid

from pydantic import BaseModel, Field, field_validator


def _sanitize_float(v: Any) -> Any:
    if v is None:
        return v
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        cleaned = re.sub(r'[^\d.-]', '', v)
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None
    return v


class ExtractedVendor(BaseModel):
    """Vendor / supplier information extracted from the quotation."""

    name: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gst_number: Optional[str] = None


class ExtractedQuotation(BaseModel):
    """Top-level quotation header information."""

    quotation_number: Optional[str] = None
    quotation_date: Optional[str] = None
    currency: Optional[str] = None
    valid_until: Optional[str] = None


class QuotationItem(BaseModel):
    """A single line-item in the quotation."""

    item_name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None

    @field_validator("quantity", "unit_price", "total_price", mode="before")
    @classmethod
    def clean_floats(cls, v: Any) -> Any:
        return _sanitize_float(v)


class Pricing(BaseModel):
    """Summary of all monetary amounts on the quotation."""

    subtotal: Optional[float] = None
    discount: Optional[float] = None
    shipping_cost: Optional[float] = None
    tax: Optional[float] = None
    grand_total: Optional[float] = None

    @field_validator("subtotal", "discount", "shipping_cost", "tax", "grand_total", mode="before")
    @classmethod
    def clean_floats(cls, v: Any) -> Any:
        return _sanitize_float(v)


class CommercialTerms(BaseModel):
    """Commercial and delivery terms of the quotation."""

    payment_terms: Optional[str] = None
    delivery_time: Optional[str] = None
    warranty: Optional[str] = None
    incoterms: Optional[str] = None


class ProcurementExtractionResult(BaseModel):
    """
    Complete structured output of procurement extraction.

    Represents a single procurement quotation in a machine-readable format.
    """

    vendor: Optional[ExtractedVendor] = None
    quotation: Optional[ExtractedQuotation] = None
    items: list[QuotationItem] = Field(default_factory=list)
    pricing: Optional[Pricing] = None
    commercial_terms: Optional[CommercialTerms] = None


class ExtractionAgentResult(BaseModel):
    """
    Wrapper returned by ExtractionAgent.extract().

    Always has the same shape regardless of success or failure so that
    downstream consumers can rely on a consistent contract.

    ``quotation_id`` can be populated by the caller before persisting
    to the database so the result is directly linkable to its source
    Quotation record without any schema changes.
    """

    success: bool
    quotation_id: Optional[uuid.UUID] = None   # set by caller before persistence
    data: Optional[ProcurementExtractionResult] = None
    errors: list[str] = Field(default_factory=list)
    raw_llm_response: Optional[str] = None
