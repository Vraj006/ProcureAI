"""
Compliance Service — pure deterministic rule-based validation.

Evaluates a single ExtractedQuotation against a fixed set of procurement
compliance rules. No database access. No LLM calls. No side effects.

Rule categories:
  1. Document Completeness     — mandatory fields must be present
  2. Commercial Terms          — important terms should be present
  3. Pricing Validation        — financial values must not be negative
  4. Date Validation           — quotation must not be expired or post-dated
  5. Items Validation          — each line-item must have valid quantities / prices

Status determination:
  COMPLIANT            — zero issues
  PARTIALLY_COMPLIANT  — one or more WARNINGs, zero ERRORs
  NON_COMPLIANT        — one or more ERRORs
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

from app.core.logging import get_logger
from app.models.extracted_quotation import ExtractedQuotation, ExtractedQuotationItem
from app.schemas.compliance_schema import (
    ComplianceIssue,
    ComplianceStatus,
    QuotationCompliance,
    Severity,
)

logger = get_logger(__name__)

# Common date formats the LLM might produce
_DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%m/%d/%Y",
    "%d %b %Y",
    "%d %B %Y",
    "%B %d, %Y",
]

_TODAY: date = date.today()   # anchored per-process; tests may monkeypatch


def _parse_date(text: str) -> Optional[date]:
    """Try to parse a date string using common formats. Returns None on failure."""
    if not text:
        return None
    text = text.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _to_float(value) -> Optional[float]:
    """Safely coerce Numeric / Decimal / float / None → float."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class ComplianceService:
    """
    Evaluates a single ExtractedQuotation for procurement compliance.

    Usage::

        svc = ComplianceService()
        result = svc.evaluate(eq, items=list(eq.items))
    """

    def evaluate(
        self,
        eq: ExtractedQuotation,
        items: list[ExtractedQuotationItem] | None = None,
    ) -> QuotationCompliance:
        """
        Run all compliance checks against one extracted quotation.

        Args:
            eq:    ExtractedQuotation ORM instance.
            items: Pre-fetched list of line items (avoids lazy-load in tests).

        Returns:
            QuotationCompliance with issues, counts, and overall status.
        """
        issues: list[ComplianceIssue] = []
        passed: list[str] = []
        items = items or []

        self._check_document_completeness(eq, issues, passed)
        self._check_commercial_terms(eq, issues, passed)
        self._check_pricing(eq, issues, passed)
        self._check_dates(eq, issues, passed)
        self._check_items(items, issues, passed)

        error_count   = sum(1 for i in issues if i.severity == Severity.ERROR)
        warning_count = sum(1 for i in issues if i.severity == Severity.WARNING)

        if error_count > 0:
            status = ComplianceStatus.NON_COMPLIANT
        elif warning_count > 0:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            status = ComplianceStatus.COMPLIANT

        logger.info(
            "Compliance for quotation_id=%s  vendor=%s  status=%s  errors=%d  warnings=%d",
            eq.quotation_id, eq.vendor_name, status.value, error_count, warning_count,
        )

        return QuotationCompliance(
            quotation_id=eq.quotation_id,
            vendor_name=eq.vendor_name,
            status=status,
            passed_checks=len(passed),
            failed_checks=error_count,
            warning_count=warning_count,
            issues=issues,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _add(
        name: str,
        ok: bool,
        severity: Severity,
        message: str,
        issues: list[ComplianceIssue],
        passed: list[str],
    ) -> None:
        """Record one check result into the appropriate list."""
        if ok:
            passed.append(name)
        else:
            issues.append(ComplianceIssue(check_name=name, severity=severity, message=message))

    # ── 1. Document completeness ─────────────────────────────────────────

    def _check_document_completeness(
        self,
        eq: ExtractedQuotation,
        issues: list[ComplianceIssue],
        passed: list[str],
    ) -> None:
        a = self._add

        a("vendor_name_present",
          bool(eq.vendor_name and eq.vendor_name.strip()),
          Severity.ERROR,
          "Vendor name is missing.",
          issues, passed)

        a("gst_number_present",
          bool(eq.vendor_gst_number and eq.vendor_gst_number.strip()),
          Severity.WARNING,
          "GST / Tax number is not provided.",
          issues, passed)

        a("quotation_number_present",
          bool(eq.quotation_number and eq.quotation_number.strip()),
          Severity.ERROR,
          "Quotation number is missing.",
          issues, passed)

        a("quotation_date_present",
          bool(eq.quotation_date and eq.quotation_date.strip()),
          Severity.WARNING,
          "Quotation date is not provided.",
          issues, passed)

        a("currency_present",
          bool(eq.currency and eq.currency.strip()),
          Severity.ERROR,
          "Currency is missing.",
          issues, passed)

        a("grand_total_present",
          _to_float(eq.grand_total) is not None,
          Severity.ERROR,
          "Grand total amount is missing.",
          issues, passed)

    # ── 2. Commercial terms ──────────────────────────────────────────────

    def _check_commercial_terms(
        self,
        eq: ExtractedQuotation,
        issues: list[ComplianceIssue],
        passed: list[str],
    ) -> None:
        a = self._add

        a("payment_terms_present",
          bool(eq.payment_terms and eq.payment_terms.strip()),
          Severity.WARNING,
          "Payment terms are not specified.",
          issues, passed)

        a("delivery_time_present",
          bool(eq.delivery_time and eq.delivery_time.strip()),
          Severity.WARNING,
          "Delivery time is not specified.",
          issues, passed)

        a("warranty_present",
          bool(eq.warranty and eq.warranty.strip()),
          Severity.WARNING,
          "Warranty information is not provided.",
          issues, passed)

    # ── 3. Pricing validation ────────────────────────────────────────────

    def _check_pricing(
        self,
        eq: ExtractedQuotation,
        issues: list[ComplianceIssue],
        passed: list[str],
    ) -> None:
        a = self._add

        grand_total = _to_float(eq.grand_total)
        a("grand_total_non_negative",
          grand_total is None or grand_total >= 0,
          Severity.ERROR,
          f"Grand total is negative ({grand_total}).",
          issues, passed)

        subtotal = _to_float(eq.subtotal)
        a("subtotal_non_negative",
          subtotal is None or subtotal >= 0,
          Severity.ERROR,
          f"Subtotal is negative ({subtotal}).",
          issues, passed)

        discount = _to_float(eq.discount)
        a("discount_non_negative",
          discount is None or discount >= 0,
          Severity.ERROR,
          f"Discount is negative ({discount}).",
          issues, passed)

        tax = _to_float(eq.tax)
        a("tax_non_negative",
          tax is None or tax >= 0,
          Severity.ERROR,
          f"Tax amount is negative ({tax}).",
          issues, passed)

        shipping = _to_float(eq.shipping_cost)
        a("shipping_cost_non_negative",
          shipping is None or shipping >= 0,
          Severity.ERROR,
          f"Shipping cost is negative ({shipping}).",
          issues, passed)

    # ── 4. Date validation ───────────────────────────────────────────────

    def _check_dates(
        self,
        eq: ExtractedQuotation,
        issues: list[ComplianceIssue],
        passed: list[str],
    ) -> None:
        a = self._add
        today = _TODAY

        # valid_until — must not be in the past
        if eq.valid_until:
            parsed = _parse_date(eq.valid_until)
            if parsed is not None:
                a("valid_until_not_expired",
                  parsed >= today,
                  Severity.ERROR,
                  f"Quotation has expired (valid until {eq.valid_until}, today is {today}).",
                  issues, passed)
            # If unparseable, skip silently (do not penalise)

        # quotation_date — must not be in the future
        if eq.quotation_date:
            parsed = _parse_date(eq.quotation_date)
            if parsed is not None:
                a("quotation_date_not_future",
                  parsed <= today,
                  Severity.WARNING,
                  f"Quotation date is in the future ({eq.quotation_date}).",
                  issues, passed)

    # ── 5. Items validation ──────────────────────────────────────────────

    def _check_items(
        self,
        items: list[ExtractedQuotationItem],
        issues: list[ComplianceIssue],
        passed: list[str],
    ) -> None:
        if not items:
            return  # no items present → skip item checks

        a = self._add

        # Aggregate checks across all items
        missing_names    = [i for i in items if not (i.item_name and i.item_name.strip())]
        bad_quantities   = [i for i in items if (_to_float(i.quantity) is not None and (_to_float(i.quantity) or 0) <= 0)]
        bad_unit_prices  = [i for i in items if (_to_float(i.unit_price) is not None and (_to_float(i.unit_price) or 0) < 0)]
        bad_total_prices = [i for i in items if (_to_float(i.total_price) is not None and (_to_float(i.total_price) or 0) < 0)]

        a("items_item_name_present",
          len(missing_names) == 0,
          Severity.WARNING,
          f"{len(missing_names)} item(s) are missing an item name.",
          issues, passed)

        a("items_quantity_positive",
          len(bad_quantities) == 0,
          Severity.ERROR,
          f"{len(bad_quantities)} item(s) have a quantity ≤ 0.",
          issues, passed)

        a("items_unit_price_non_negative",
          len(bad_unit_prices) == 0,
          Severity.ERROR,
          f"{len(bad_unit_prices)} item(s) have a negative unit price.",
          issues, passed)

        a("items_total_price_non_negative",
          len(bad_total_prices) == 0,
          Severity.ERROR,
          f"{len(bad_total_prices)} item(s) have a negative total price.",
          issues, passed)
