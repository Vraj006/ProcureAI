"""
Recommendation Agent.

Synthesises ComparisonResult + ComplianceResult into a structured
vendor recommendation. Pipeline:

  1.  Deterministically filter out NON_COMPLIANT vendors.
  2.  If no eligible vendor → return "No Recommendation".
  3.  Pick the eligible vendor with the lowest price rank.
  4.  Compute a confidence score from hard metrics.
  5.  Call LLMService for human-readable reasoning / strengths / risks.
  6.  On LLM failure → return deterministic result with reasoning=None.
  7.  Validate and return RecommendationAgentResult.

The LLM is used ONLY for narrative generation — it never influences
which vendor is recommended.
"""

from __future__ import annotations

import json
from typing import Optional

from app.core.logging import get_logger
from app.human_review.schemas import HumanFeedback
from app.schemas.comparison_schema import ComparisonResult, VendorComparison
from app.schemas.compliance_schema import ComplianceResult, ComplianceStatus
from app.schemas.recommendation_schema import (
    RecommendationAgentResult,
    RecommendationResult,
)
from app.services.llm_service import LLMService

logger = get_logger(__name__)

# ── LLM reasoning prompts ──────────────────────────────────────────────────
_REASONING_SYSTEM_PROMPT = """\
You are a senior procurement advisor.
Given a structured comparison and compliance report, generate a JSON reasoning
for why the nominated vendor is recommended.

RULES:
1. Base your answer ONLY on the provided data.
2. NEVER invent facts.
3. NEVER recommend a vendor marked NON_COMPLIANT.
4. If human reviewer feedback is present, respect it and explain any
   change in recommendation.
5. Return ONLY a valid JSON object — no markdown, no prose outside JSON.

OUTPUT FORMAT:
{
  "recommended_vendor": "<Exact Vendor Name String>",
  "reasoning": "<2-3 sentence factual explanation>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "risks": ["<risk 1>"],
  "alternatives": ["<alt vendor 1>"]
}"""


def _build_reasoning_user_prompt(
    recommended_vendor: str,
    comparison: ComparisonResult,
    compliance: ComplianceResult,
    alternatives: list[str],
    human_feedback: Optional[HumanFeedback] = None,
) -> str:
    comp_lines = [
        f"Recommended vendor: {recommended_vendor}",
        f"Currency: {comparison.currency or 'N/A'} ({'consistent' if comparison.currency_consistent else 'INCONSISTENT'})",
        f"Lowest price vendor: {comparison.lowest_price_vendor} at {comparison.lowest_price}",
        f"Highest discount vendor: {comparison.highest_discount_vendor}",
        f"Fastest delivery vendor: {comparison.fastest_delivery_vendor}",
        f"Best warranty vendor: {comparison.best_warranty_vendor}",
    ]
    ranking_lines = "\n".join(
        f"  {v.rank}. {v.vendor_name}: {comparison.currency or ''} {v.grand_total}"
        + (f", discount={v.discount}" if v.discount else "")
        + (f", delivery={v.delivery_time}" if v.delivery_time else "")
        + (f", warranty={v.warranty}" if v.warranty else "")
        for v in comparison.vendor_rankings
    )
    compliance_lines = "\n".join(
        f"  {qr.vendor_name}: {qr.status.value} ({qr.failed_checks} errors, {qr.warning_count} warnings)"
        for qr in compliance.quotation_results
    )
    alt_line = ", ".join(alternatives) if alternatives else "None"
    prompt = (
        "Comparison metrics:\n" + "\n".join(comp_lines)
        + "\n\nVendor rankings:\n" + ranking_lines
        + "\n\nCompliance statuses:\n" + compliance_lines
        + f"\n\nEligible alternatives (not recommended): {alt_line}"
    )

    # ── Inject human reviewer feedback if present ──────────────────────
    if human_feedback is not None:
        feedback_parts = [
            f"\n\nREVIEWER FEEDBACK (must be respected):",
            f"Review decision: {human_feedback.status.value}",
        ]
        if human_feedback.rejection_reason:
            feedback_parts.append(f"Rejection reason: {human_feedback.rejection_reason}")
        if human_feedback.reviewer_comments:
            feedback_parts.append(f"Reviewer comments: {human_feedback.reviewer_comments}")
        if human_feedback.selected_vendor:
            feedback_parts.append(f"Reviewer's preferred vendor: {human_feedback.selected_vendor}")
        if human_feedback.additional_notes:
            feedback_parts.append(f"Additional notes: {human_feedback.additional_notes}")
        feedback_parts.append(
            "INSTRUCTIONS: Respect this feedback. Reconsider alternatives. "
            "Explain any changes in your recommendation. "
            "NEVER recommend a NON_COMPLIANT vendor."
        )
        prompt += "\n".join(feedback_parts)

    prompt += "\n\nGenerate the reasoning JSON for the recommended vendor."
    return prompt


# ── Confidence score ───────────────────────────────────────────────────────

def _compute_confidence(
    vendor_name: str,
    comparison: ComparisonResult,
    compliance: ComplianceResult,
    eligible_count: int,
) -> int:
    score = 40  # base

    # Compliance tier bonus
    qr = next((r for r in compliance.quotation_results if r.vendor_name == vendor_name), None)
    if qr:
        if qr.status == ComplianceStatus.COMPLIANT:
            score += 25
        elif qr.status == ComplianceStatus.PARTIALLY_COMPLIANT:
            score += 10

    # Price rank bonus
    vr = next((v for v in comparison.vendor_rankings if v.vendor_name == vendor_name), None)
    if vr and vr.rank == 1:
        score += 15      # lowest price

    # Metric win bonuses
    if comparison.best_warranty_vendor == vendor_name:
        score += 8
    if comparison.fastest_delivery_vendor == vendor_name:
        score += 7
    if comparison.highest_discount_vendor == vendor_name:
        score += 5

    # Single option penalty (no real competition)
    if eligible_count == 1:
        score -= 10

    return max(0, min(100, score))


# ── Main Agent ─────────────────────────────────────────────────────────────

class RecommendationAgent:
    """
    Produces a structured vendor recommendation from pre-computed results.

    Does NOT access the database.  Does NOT call the Extraction,
    Comparison, or Compliance agents.

    Args:
        llm_service: Optional LLMService for narrative generation.
                     If None, the recommendation is purely deterministic.
    """

    def __init__(self, llm_service: LLMService | None = None) -> None:
        self._llm = llm_service

    # ── Public interface ───────────────────────────────────────────────

    def recommend(
        self,
        comparison_result: Optional[ComparisonResult],
        compliance_result: Optional[ComplianceResult],
        human_feedback: Optional[HumanFeedback] = None,
    ) -> RecommendationAgentResult:
        """
        Determine the best vendor from comparison and compliance data.

        Args:
            comparison_result: Output from ComparisonAgent.
            compliance_result: Output from ComplianceAgent.
            human_feedback:    Optional reviewer feedback for HITL re-runs.
                               When present it is included in the LLM prompt
                               so the model can reconsider alternatives.

        Returns:
            RecommendationAgentResult — always the same shape.
        """
        # ── Guard: missing upstream results ─────────────────────────────
        if comparison_result is None or compliance_result is None:
            return RecommendationAgentResult(
                success=False,
                errors=["comparison_result and compliance_result are both required."],
            )

        logger.info(
            "RecommendationAgent.recommend()  vendors=%d",
            len(comparison_result.vendor_rankings),
        )

        # ── Step 1: Identify non-compliant vendors ───────────────────────
        non_compliant_names: set[str] = {
            qr.vendor_name
            for qr in compliance_result.quotation_results
            if qr.status == ComplianceStatus.NON_COMPLIANT and qr.vendor_name
        }

        # ── Step 2: Filter eligible vendors ─────────────────────────────
        eligible: list[VendorComparison] = [
            v for v in comparison_result.vendor_rankings
            if v.vendor_name and v.vendor_name not in non_compliant_names
        ]
        # Sort by rank (already ordered, but explicit is safer)
        eligible.sort(key=lambda v: (v.rank, v.vendor_name or ""))

        # ── Step 3: No eligible vendor ───────────────────────────────────
        if not eligible:
            logger.warning("No eligible (non-NON_COMPLIANT) vendor found.")
            return RecommendationAgentResult(
                success=True,
                data=RecommendationResult(
                    is_no_recommendation=True,
                    confidence_score=0,
                ),
            )

        # ── Step 4: Pick recommended vendor ─────────────────────────────
        recommended: Optional[VendorComparison] = None
        
        if human_feedback and human_feedback.selected_vendor:
            for v in eligible:
                if v.vendor_name == human_feedback.selected_vendor:
                    logger.info("HumanReviewer override engaged — manually switching selected vendor to %s", v.vendor_name)
                    recommended = v
                    break

        if recommended is None:
            recommended = eligible[0]
            
        alternatives = [v.vendor_name for v in eligible if v.vendor_name and v.vendor_name != recommended.vendor_name]
        confidence = _compute_confidence(
            recommended.vendor_name,
            comparison_result,
            compliance_result,
            len(eligible),
        )

        # ── Step 5: LLM reasoning ────────────────────────────────────────
        reasoning: Optional[str] = None
        strengths: list[str] = []
        risks: list[str] = []
        llm_alternatives: list[str] = alternatives   # default to deterministic
        is_deterministic_fallback = False

        if self._llm is not None:
            try:
                user_prompt = _build_reasoning_user_prompt(
                    recommended.vendor_name,
                    comparison_result,
                    compliance_result,
                    alternatives,
                    human_feedback=human_feedback,    # ← HITL context
                )
                raw = self._llm.complete_json(
                    system_prompt=_REASONING_SYSTEM_PROMPT,
                    user_content=user_prompt,
                )
                parsed = json.loads(raw)
                
                llm_recommended = parsed.get("recommended_vendor")
                if llm_recommended and isinstance(llm_recommended, str):
                    if llm_recommended != recommended.vendor_name:
                        logger.info("LLM dynamically engaged NLP override! Switching selected vendor to %s", llm_recommended)
                    final_vendor = llm_recommended
                else:
                    final_vendor = recommended.vendor_name
                    
                reasoning        = parsed.get("reasoning")
                strengths        = parsed.get("strengths") or []
                risks            = parsed.get("risks") or []
                llm_alternatives = parsed.get("alternatives") or alternatives
                logger.info("LLM reasoning generated for vendor=%s", final_vendor)
            except Exception as exc:
                logger.warning("LLM reasoning failed (non-fatal): %s", exc)
                is_deterministic_fallback = True
                final_vendor = recommended.vendor_name
        else:
            final_vendor = recommended.vendor_name

        return RecommendationAgentResult(
            success=True,
            data=RecommendationResult(
                recommended_vendor=final_vendor,
                confidence_score=confidence,
                reasoning=reasoning,
                strengths=strengths,
                risks=risks,
                alternatives=llm_alternatives,
                is_no_recommendation=False,
                is_deterministic_fallback=is_deterministic_fallback,
            ),
        )
