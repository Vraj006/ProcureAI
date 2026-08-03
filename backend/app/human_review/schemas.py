"""
Human-in-the-Loop (HITL) review schemas.

Defines the data contracts for reviewer decisions, feedback payloads,
and the structured result that the LangGraph node returns to the workflow.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewStatus(str, enum.Enum):
    """Lifecycle state of a human review decision."""

    PENDING_REVIEW    = "pending_review"
    APPROVED          = "approved"
    REJECTED          = "rejected"
    REQUIRES_CHANGES  = "requires_changes"


class HumanFeedback(BaseModel):
    """
    Structured feedback submitted by a procurement reviewer.

    Validation rules enforced by HumanReviewService:
      - APPROVED         → ``selected_vendor`` is required.
      - REJECTED         → ``rejection_reason`` is required.
      - REQUIRES_CHANGES → ``reviewer_comments`` is encouraged (not enforced).
    """

    project_id:           uuid.UUID
    recommended_vendor:   Optional[str]      = None  # AI recommendation being reviewed
    selected_vendor:      Optional[str]      = None  # reviewer's preferred vendor
    status:               ReviewStatus
    reviewer_comments:    Optional[str]      = None
    rejection_reason:     Optional[str]      = None
    additional_notes:     Optional[str]      = None
    review_timestamp:     Optional[datetime] = Field(default_factory=datetime.utcnow)


class HumanReviewResult(BaseModel):
    """
    Normalised result produced by HumanReviewService.process().

    ``approved``       — True only when status is APPROVED.
    ``requires_rerun`` — True for REJECTED and REQUIRES_CHANGES;
                         signals the workflow to re-run the Recommendation node.
    ``feedback``       — the original HumanFeedback payload (None if no feedback yet).
    """

    status:           ReviewStatus
    approved:         bool
    requires_rerun:   bool
    feedback:         Optional[HumanFeedback] = None
