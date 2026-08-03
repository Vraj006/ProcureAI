"""
Pydantic schemas for structured comparison results.

All winner/ranking fields are Optional so a partial result can be
returned even when some metrics are unparseable.
"""

import uuid
from typing import Optional

from pydantic import BaseModel, Field


class VendorComparison(BaseModel):
    """Per-vendor data row in the final ranking table."""

    vendor_name: Optional[str] = None
    grand_total: Optional[float] = None
    discount: Optional[float] = None
    delivery_time: Optional[str] = None  # raw string preserved from extraction
    warranty: Optional[str] = None       # raw string preserved from extraction
    rank: int                            # 1 = cheapest (lowest grand_total)


class ComparisonResult(BaseModel):
    """
    Structured output of the Comparison Service.

    All 'winner' fields are Optional because it is possible that a given
    metric was not present in any of the extracted quotations.
    """

    # ── Category winners ────────────────────────────────────────────────
    lowest_price_vendor: Optional[str] = None
    lowest_price: Optional[float] = None
    highest_discount_vendor: Optional[str] = None
    fastest_delivery_vendor: Optional[str] = None
    best_warranty_vendor: Optional[str] = None

    # ── Currency ─────────────────────────────────────────────────────────
    currency_consistent: bool
    currency: Optional[str] = None   # None if inconsistent or unavailable

    # ── Vendor ranking table ─────────────────────────────────────────────
    vendor_rankings: list[VendorComparison] = Field(default_factory=list)

    # ── LLM-generated natural-language summary (set by agent, not service)
    summary: Optional[str] = None


class ComparisonAgentResult(BaseModel):
    """
    Wrapper returned by ComparisonAgent.compare().

    Always has the same shape regardless of success or failure.
    """

    success: bool
    project_id: Optional[uuid.UUID] = None
    data: Optional[ComparisonResult] = None
    errors: list[str] = Field(default_factory=list)
