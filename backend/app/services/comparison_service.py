"""
Comparison Service — pure deterministic business logic.

Accepts a list of ExtractedQuotation ORM objects and computes:
  - Category winners (price, discount, delivery, warranty)
  - Currency consistency
  - Vendor ranking by grand total

No database access.  No LLM calls.  No side effects.
"""

import re
from decimal import Decimal
from typing import Optional

from app.core.logging import get_logger
from app.models.extracted_quotation import ExtractedQuotation
from app.schemas.comparison_schema import ComparisonResult, VendorComparison

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_TIME_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(day|week|month|year)s?",
    re.IGNORECASE,
)

_WARRANTY_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(month|year)s?",
    re.IGNORECASE,
)


def _parse_delivery_days(text: str) -> Optional[int]:
    """
    Convert a delivery time string to an equivalent number of days.

    Handles: "4 weeks", "30 days", "2 months", "1 year".
    Returns None for ambiguous or unparseable strings so ranking is skipped.
    """
    if not text:
        return None
    match = _TIME_PATTERN.search(text)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2).lower()
    multipliers = {"day": 1, "week": 7, "month": 30, "year": 365}
    return int(value * multipliers[unit])


def _parse_warranty_months(text: str) -> Optional[int]:
    """
    Convert a warranty string to an equivalent number of months.

    Handles: "12 months", "2 years", "1 year".
    Returns None for ambiguous or unparseable strings.
    """
    if not text:
        return None
    match = _WARRANTY_PATTERN.search(text)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2).lower()
    if unit == "month":
        return int(value)
    elif unit == "year":
        return int(value * 12)
    return None


def _to_float(value) -> Optional[float]:
    """Safely coerce Numeric / Decimal / float / None to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Comparison Service
# ---------------------------------------------------------------------------


class ComparisonService:
    """
    Deterministic comparison of multiple extracted procurement quotations.

    Usage::

        service = ComparisonService()
        result = service.compare(extracted_quotations)
    """

    def compare(self, extracted: list[ExtractedQuotation]) -> ComparisonResult:
        """
        Compare extracted quotations and produce a structured ComparisonResult.

        Args:
            extracted: List of ExtractedQuotation ORM instances (≥ 2 expected).

        Returns:
            ComparisonResult with winners, rankings, and currency info.
        """
        logger.info("ComparisonService comparing %d quotations", len(extracted))

        # ── Currency consistency ─────────────────────────────────────────
        currencies = {eq.currency for eq in extracted if eq.currency}
        currency_consistent = len(currencies) == 1
        currency = next(iter(currencies)) if len(currencies) == 1 else None

        # ── Separate quotations by data availability ─────────────────────
        with_total = [(eq, _to_float(eq.grand_total)) for eq in extracted
                      if _to_float(eq.grand_total) is not None]
        without_total = [eq for eq in extracted if _to_float(eq.grand_total) is None]

        # ── Sort by price ascending → forms the ranking ──────────────────
        ranked = sorted(with_total, key=lambda x: x[1])

        # ── Build VendorComparison rows ──────────────────────────────────
        vendor_rankings: list[VendorComparison] = []
        for rank, (eq, total) in enumerate(ranked, start=1):
            vendor_rankings.append(VendorComparison(
                vendor_name=eq.vendor_name,
                grand_total=total,
                discount=_to_float(eq.discount),
                delivery_time=eq.delivery_time,
                warranty=eq.warranty,
                rank=rank,
            ))
        # Append un-ranked (no price) at the end
        for eq in without_total:
            vendor_rankings.append(VendorComparison(
                vendor_name=eq.vendor_name,
                grand_total=None,
                discount=_to_float(eq.discount),
                delivery_time=eq.delivery_time,
                warranty=eq.warranty,
                rank=len(ranked) + 1,
            ))

        # ── Category winners ─────────────────────────────────────────────
        lowest_price_vendor: Optional[str] = ranked[0][0].vendor_name if ranked else None
        lowest_price: Optional[float] = ranked[0][1] if ranked else None

        # Highest discount
        with_discount = [(eq, _to_float(eq.discount)) for eq in extracted
                         if _to_float(eq.discount) is not None]
        highest_discount_vendor: Optional[str] = None
        if with_discount:
            best_disc = max(with_discount, key=lambda x: x[1])
            highest_discount_vendor = best_disc[0].vendor_name

        # Fastest delivery (smallest days value = best)
        delivery_parsed = [
            (eq, _parse_delivery_days(eq.delivery_time))
            for eq in extracted
        ]
        delivery_valid = [(eq, d) for eq, d in delivery_parsed if d is not None]
        fastest_delivery_vendor: Optional[str] = None
        if delivery_valid:
            fastest_delivery_vendor = min(delivery_valid, key=lambda x: x[1])[0].vendor_name

        # Best warranty (highest months value = best)
        warranty_parsed = [
            (eq, _parse_warranty_months(eq.warranty))
            for eq in extracted
        ]
        warranty_valid = [(eq, m) for eq, m in warranty_parsed if m is not None]
        best_warranty_vendor: Optional[str] = None
        if warranty_valid:
            best_warranty_vendor = max(warranty_valid, key=lambda x: x[1])[0].vendor_name

        result = ComparisonResult(
            lowest_price_vendor=lowest_price_vendor,
            lowest_price=lowest_price,
            highest_discount_vendor=highest_discount_vendor,
            fastest_delivery_vendor=fastest_delivery_vendor,
            best_warranty_vendor=best_warranty_vendor,
            currency_consistent=currency_consistent,
            currency=currency,
            vendor_rankings=vendor_rankings,
            summary=None,  # filled by ComparisonAgent after optional LLM call
        )

        logger.info(
            "Comparison complete — lowest=%s  discount=%s  delivery=%s  warranty=%s  currency_ok=%s",
            lowest_price_vendor,
            highest_discount_vendor,
            fastest_delivery_vendor,
            best_warranty_vendor,
            currency_consistent,
        )
        return result
