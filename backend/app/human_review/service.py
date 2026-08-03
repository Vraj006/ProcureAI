"""
Human Review Service — pure deterministic validation.

Validates reviewer decisions and produces a HumanReviewResult.
No database access. No LLM calls. No side effects.

Status → (approved, requires_rerun) mapping:
  APPROVED         → (True,  False)
  REJECTED         → (False, True)
  REQUIRES_CHANGES → (False, True)
  PENDING_REVIEW   → (False, False)
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.human_review.schemas import HumanFeedback, HumanReviewResult, ReviewStatus

logger = get_logger(__name__)

# Map each status → (approved, requires_rerun)
_STATUS_FLAGS: dict[ReviewStatus, tuple[bool, bool]] = {
    ReviewStatus.APPROVED:        (True,  False),
    ReviewStatus.REJECTED:        (False, True),
    ReviewStatus.REQUIRES_CHANGES:(False, True),
    ReviewStatus.PENDING_REVIEW:  (False, False),
}


class HumanReviewService:
    """
    Validates and processes a HumanFeedback payload.

    Raises:
        ValueError: when the feedback fails domain validation.
    """

    def process(self, feedback: HumanFeedback) -> HumanReviewResult:
        """
        Validate and convert HumanFeedback into a structured HumanReviewResult.

        Args:
            feedback: Reviewer-submitted feedback payload.

        Returns:
            HumanReviewResult with ``approved`` and ``requires_rerun`` flags.

        Raises:
            ValueError: if required fields for the given status are missing.
        """
        errors = self._validate(feedback)
        if errors:
            raise ValueError(f"Human review validation failed: {'; '.join(errors)}")

        approved, requires_rerun = _STATUS_FLAGS[feedback.status]

        logger.info(
            "HumanReviewService.process()  status=%s  approved=%s  requires_rerun=%s",
            feedback.status.value, approved, requires_rerun,
        )
        return HumanReviewResult(
            status=feedback.status,
            approved=approved,
            requires_rerun=requires_rerun,
            feedback=feedback,
        )

    # ── Validation ────────────────────────────────────────────────────────

    @staticmethod
    def _validate(feedback: HumanFeedback) -> list[str]:
        """Return a list of validation error messages (empty = valid)."""
        errors: list[str] = []

        if feedback.status == ReviewStatus.APPROVED:
            if not (feedback.selected_vendor and feedback.selected_vendor.strip()):
                errors.append(
                    "``selected_vendor`` is required when status is APPROVED."
                )

        if feedback.status == ReviewStatus.REJECTED:
            if not (feedback.rejection_reason and feedback.rejection_reason.strip()):
                errors.append(
                    "``rejection_reason`` is required when status is REJECTED."
                )

        return errors
