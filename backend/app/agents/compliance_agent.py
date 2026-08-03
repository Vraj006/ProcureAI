"""
Compliance Agent.

Orchestrates project-level compliance evaluation:

  project_id
    ↓  fetch from DB
  ExtractedQuotation list
    ↓  per-quotation
  ComplianceService.evaluate()
    ↓  aggregate
  ComplianceResult
    ↓  optional Mistral call
  summary (factual, no recommendations)
    ↓
  ComplianceAgentResult
"""

import json
import uuid

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.repositories.extracted_quotation_repository import (
    ExtractedQuotationRepository,
)
from app.schemas.compliance_schema import (
    ComplianceAgentResult,
    ComplianceResult,
    ComplianceStatus,
)
from app.services.compliance_service import ComplianceService
from app.services.llm_service import LLMService

logger = get_logger(__name__)

# ── LLM summary prompt ─────────────────────────────────────────────────────
_SUMMARY_SYSTEM_PROMPT = """\
You are a senior procurement compliance analyst.
Write a concise 2-3 sentence factual summary of the compliance evaluation results.
Base your summary ONLY on the provided metrics.
Do NOT invent facts, do NOT give recommendations, do NOT use bullet points.
Respond with plain text only."""


def _build_summary_user_prompt(result: ComplianceResult) -> str:
    lines = [
        f"Project compliance evaluation — {result.total_quotations} quotation(s) assessed.",
        f"COMPLIANT: {result.compliant_count}",
        f"PARTIALLY_COMPLIANT: {result.partially_compliant_count}",
        f"NON_COMPLIANT: {result.non_compliant_count}",
    ]
    for qr in result.quotation_results:
        issue_summary = (
            f"{qr.failed_checks} error(s), {qr.warning_count} warning(s)"
            if qr.failed_checks or qr.warning_count
            else "no issues"
        )
        lines.append(
            f"  • {qr.vendor_name or 'Unknown vendor'}: {qr.status.value} ({issue_summary})"
        )
    return (
        "Compliance report:\n"
        + "\n".join(lines)
        + "\n\nSummarise the above in 2-3 sentences for a procurement manager."
    )


class ComplianceAgent:
    """
    Evaluates procurement compliance for all extracted quotations in a project.

    Args:
        db:               Active SQLAlchemy session.
        llm_service:      Optional LLMService for summary generation.
        generate_summary: Set False to skip LLM call (useful in tests).
    """

    def __init__(
        self,
        db: Session,
        llm_service: LLMService | None = None,
        generate_summary: bool = True,
    ) -> None:
        self._db = db
        self._repo = ExtractedQuotationRepository(db)
        self._compliance_svc = ComplianceService()
        self._llm = llm_service
        self._generate_summary = generate_summary and llm_service is not None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def evaluate(self, project_id: uuid.UUID) -> ComplianceAgentResult:
        """
        Run compliance evaluation for all extracted quotations in a project.

        An empty project (zero quotations) is valid — it returns a result
        with all counts at zero rather than an error.

        Args:
            project_id: UUID of the ProcurementProject.

        Returns:
            ComplianceAgentResult — same shape on success and failure.
        """
        logger.info("ComplianceAgent.evaluate() project_id=%s", project_id)

        # ── Step 1: Fetch extracted quotations ───────────────────────────
        try:
            extracted = self._repo.get_by_project_id(project_id)
        except Exception as exc:
            logger.error("DB fetch failed: %s", exc)
            return ComplianceAgentResult(
                success=False,
                errors=[f"Database error: {exc}"],
            )

        # ── Step 2: Evaluate each quotation ──────────────────────────────
        quotation_results = []
        for eq in extracted:
            try:
                items = list(eq.items)   # materialise lazy relationship in active session
            except Exception:
                items = []

            qr = self._compliance_svc.evaluate(eq, items)
            quotation_results.append(qr)

        # ── Step 3: Aggregate project-level counts ───────────────────────
        compliant_count          = sum(1 for r in quotation_results if r.status == ComplianceStatus.COMPLIANT)
        partially_compliant_count = sum(1 for r in quotation_results if r.status == ComplianceStatus.PARTIALLY_COMPLIANT)
        non_compliant_count      = sum(1 for r in quotation_results if r.status == ComplianceStatus.NON_COMPLIANT)

        result = ComplianceResult(
            project_id=project_id,
            total_quotations=len(extracted),
            compliant_count=compliant_count,
            partially_compliant_count=partially_compliant_count,
            non_compliant_count=non_compliant_count,
            quotation_results=quotation_results,
        )

        # ── Step 4: Optional LLM summary ─────────────────────────────────
        if self._generate_summary and self._llm is not None:
            try:
                user_prompt = _build_summary_user_prompt(result)
                raw = self._llm.complete_json(
                    system_prompt=_SUMMARY_SYSTEM_PROMPT,
                    user_content=user_prompt,
                )
                # LLM is in json_object mode — try to unwrap {"summary":"..."}
                try:
                    parsed = json.loads(raw)
                    result.summary = parsed.get("summary") or parsed.get("text") or raw
                except (json.JSONDecodeError, AttributeError):
                    result.summary = raw.strip()
            except Exception as exc:
                logger.warning("LLM summary generation failed (non-fatal): %s", exc)

        logger.info(
            "Compliance evaluation complete — total=%d  compliant=%d  partial=%d  non=%d",
            result.total_quotations,
            compliant_count,
            partially_compliant_count,
            non_compliant_count,
        )
        return ComplianceAgentResult(success=True, data=result)
