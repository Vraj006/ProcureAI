"""
LangGraph state definition for the ProcureAI procurement workflow.

ProcurementState flows through nodes:
  Comparison → Compliance → Recommendation → Human Review
                                ↑                    |
                                └── (requires_rerun) ┘

The ``errors`` field uses an accumulator reducer so node errors are
appended rather than replaced as state propagates through the graph.
"""

from __future__ import annotations

import operator
import uuid
from typing import Annotated, Optional, TypedDict

from app.human_review.schemas import HumanFeedback, HumanReviewResult
from app.schemas.comparison_schema import ComparisonResult
from app.schemas.compliance_schema import ComplianceResult
from app.schemas.recommendation_schema import RecommendationResult


class ProcurementState(TypedDict):
    """
    Shared state threaded through all LangGraph nodes.

    Fields
    ------
    project_id            : UUID identifying the ProcurementProject.
    comparison_result     : Output from ComparisonNode.
    compliance_result     : Output from ComplianceNode.
    recommendation_result : Output from RecommendationNode.
    human_review_result   : Output from HumanReviewNode.
    human_feedback        : Reviewer-submitted HumanFeedback (external input).
    feedback_processed    : Set True by HumanReviewNode after processing feedback
                            with requires_rerun=True; prevents infinite loop on
                            subsequent iterations.
    errors                : Accumulator — each node appends its own errors.
    """

    project_id:             uuid.UUID
    comparison_result:      Optional[ComparisonResult]
    compliance_result:      Optional[ComplianceResult]
    recommendation_result:  Optional[RecommendationResult]
    human_review_result:    Optional[HumanReviewResult]
    human_feedback:         Optional[HumanFeedback]
    feedback_processed:     bool
    errors:                 Annotated[list[str], operator.add]
