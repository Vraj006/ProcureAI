"""
Comparison Agent.

Orchestrates the vendor comparison pipeline for a ProcurementProject:

  project_id
    ↓  fetch from DB
  ExtractedQuotation list (≥ 2)
    ↓
  ComparisonService (deterministic)
    ↓
  ComparisonResult
    ↓  optional Mistral call
  summary (natural-language, factual only)
    ↓
  ComparisonAgentResult
"""

import uuid

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.repositories.extracted_quotation_repository import (
    ExtractedQuotationRepository,
)
from app.schemas.comparison_schema import ComparisonAgentResult, ComparisonResult
from app.services.comparison_service import ComparisonService
from app.services.llm_service import LLMService

logger = get_logger(__name__)

_MIN_QUOTATIONS = 2

# ── Summary prompt ────────────────────────────────────────────────────────
_SUMMARY_SYSTEM_PROMPT = """\
You are a senior procurement analyst. Write a concise 2-3 sentence business summary
based ONLY on the comparison metrics provided. Do NOT invent facts, do NOT suggest
recommendations, and do NOT include any information not present in the data.
Respond with plain text only — no bullet points, no JSON, no markdown."""


def _build_summary_user_prompt(result: ComparisonResult, vendor_count: int) -> str:
    lines = [f"Number of vendors compared: {vendor_count}"]
    if result.currency:
        lines.append(f"Currency: {result.currency} ({'consistent' if result.currency_consistent else 'INCONSISTENT'})")
    if result.lowest_price_vendor and result.lowest_price is not None:
        lines.append(f"Lowest price: {result.lowest_price_vendor} at {result.lowest_price:,.2f} {result.currency or ''}")
    if result.highest_discount_vendor:
        lines.append(f"Highest discount: {result.highest_discount_vendor}")
    if result.fastest_delivery_vendor:
        lines.append(f"Fastest delivery: {result.fastest_delivery_vendor}")
    if result.best_warranty_vendor:
        lines.append(f"Best warranty: {result.best_warranty_vendor}")

    ranking_lines = "\n".join(
        f"  {v.rank}. {v.vendor_name}: {result.currency or ''} {v.grand_total:,.2f}"
        if v.grand_total is not None
        else f"  -. {v.vendor_name}: (no price data)"
        for v in result.vendor_rankings
    )

    return (
        "Procurement comparison metrics:\n"
        + "\n".join(lines)
        + "\n\nVendor rankings by price:\n"
        + ranking_lines
        + "\n\nSummarize the above data in 2-3 sentences for a procurement manager."
    )


class ComparisonAgent:
    """
    Compares extracted quotations within a ProcurementProject.

    Requires a live SQLAlchemy Session. The LLMService is optional;
    if None is provided summary generation is skipped.
    """

    def __init__(
        self,
        db: Session,
        llm_service: LLMService | None = None,
        generate_summary: bool = True,
    ) -> None:
        self._db = db
        self._repo = ExtractedQuotationRepository(db)
        self._comparison_service = ComparisonService()
        self._llm = llm_service
        self._generate_summary = generate_summary and llm_service is not None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def compare(self, project_id: uuid.UUID) -> ComparisonAgentResult:
        """
        Run comparison for all extracted quotations for a given project.

        Args:
            project_id: UUID of the ProcurementProject to compare.

        Returns:
            ComparisonAgentResult — same shape on success and failure.
        """
        logger.info("ComparisonAgent.compare() project_id=%s", project_id)

        # ── Step 1: Fetch extracted quotations ───────────────────────────
        try:
            extracted = self._repo.get_by_project_id(project_id)
        except Exception as exc:
            logger.error("DB fetch failed for project %s: %s", project_id, exc)
            return ComparisonAgentResult(
                success=False,
                project_id=project_id,
                errors=[f"Database error: {exc}"],
            )

        if len(extracted) < _MIN_QUOTATIONS:
            return ComparisonAgentResult(
                success=False,
                project_id=project_id,
                errors=[
                    f"At least {_MIN_QUOTATIONS} extracted quotations are required for comparison. "
                    f"Found {len(extracted)}."
                ],
            )

        # ── Step 2: Run deterministic comparison ─────────────────────────
        try:
            result: ComparisonResult = self._comparison_service.compare(extracted)
        except Exception as exc:
            logger.error("Comparison logic failed: %s", exc)
            return ComparisonAgentResult(
                success=False,
                project_id=project_id,
                errors=[f"Comparison error: {exc}"],
            )

        # ── Step 3: Optionally generate LLM summary ──────────────────────
        if self._generate_summary and self._llm is not None:
            try:
                user_prompt = _build_summary_user_prompt(result, len(extracted))
                raw_summary = self._llm.complete_json(
                    system_prompt=_SUMMARY_SYSTEM_PROMPT,
                    user_content=user_prompt,
                )
                # The LLM is in json_object mode; the summary may be wrapped in {"summary": "..."}
                # Try to unwrap, otherwise use the raw text directly.
                import json
                try:
                    parsed = json.loads(raw_summary)
                    result.summary = parsed.get("summary") or parsed.get("text") or raw_summary
                except (json.JSONDecodeError, AttributeError):
                    result.summary = raw_summary.strip()
            except Exception as exc:
                # Summary generation is optional — log but do not fail the comparison
                logger.warning("LLM summary generation failed (non-fatal): %s", exc)

        logger.info(
            "Comparison agent complete — vendors=%d  summary_generated=%s",
            len(extracted),
            result.summary is not None,
        )
        return ComparisonAgentResult(
            success=True,
            project_id=project_id,
            data=result,
        )
