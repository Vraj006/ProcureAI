"""
LangGraph node factory functions.

Each factory returns a node function that:
  - Receives the current ProcurementState.
  - Invokes exactly one existing agent or service.
  - Returns only the state fields it modifies.

No business logic lives here. Nodes are thin adapters.
"""

from __future__ import annotations

from typing import Callable

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.graph.state import ProcurementState
from app.services.llm_service import LLMService

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Comparison Node
# ---------------------------------------------------------------------------

def make_comparison_node(
    db: Session,
    llm_service: LLMService | None = None,
) -> Callable[[ProcurementState], dict]:
    """Factory: node that invokes ComparisonAgent."""
    from app.agents.comparison_agent import ComparisonAgent

    def comparison_node(state: ProcurementState) -> dict:
        logger.info("[ComparisonNode] project_id=%s", state["project_id"])
        agent = ComparisonAgent(db=db, llm_service=llm_service, generate_summary=False)
        result = agent.compare(state["project_id"])

        if result.success:
            return {"comparison_result": result.data, "errors": []}

        errors = [f"[ComparisonNode] {e}" for e in result.errors]
        logger.warning("[ComparisonNode] failed: %s", result.errors)
        return {"comparison_result": None, "errors": errors}

    return comparison_node


# ---------------------------------------------------------------------------
# Compliance Node
# ---------------------------------------------------------------------------

def make_compliance_node(
    db: Session,
    llm_service: LLMService | None = None,
) -> Callable[[ProcurementState], dict]:
    """Factory: node that invokes ComplianceAgent."""
    from app.agents.compliance_agent import ComplianceAgent

    def compliance_node(state: ProcurementState) -> dict:
        logger.info("[ComplianceNode] project_id=%s", state["project_id"])
        agent = ComplianceAgent(db=db, llm_service=llm_service, generate_summary=False)
        result = agent.evaluate(state["project_id"])

        if result.success:
            return {"compliance_result": result.data, "errors": []}

        errors = [f"[ComplianceNode] {e}" for e in result.errors]
        logger.warning("[ComplianceNode] failed: %s", result.errors)
        return {"compliance_result": None, "errors": errors}

    return compliance_node


# ---------------------------------------------------------------------------
# Recommendation Node
# ---------------------------------------------------------------------------

def make_recommendation_node(
    llm_service: LLMService | None = None,
) -> Callable[[ProcurementState], dict]:
    """
    Factory: node that invokes RecommendationAgent.

    Passes ``human_feedback`` from state so that on loop iterations
    (requires_rerun) the agent can incorporate reviewer comments.
    """
    from app.agents.recommendation_agent import RecommendationAgent

    def recommendation_node(state: ProcurementState) -> dict:
        logger.info("[RecommendationNode] project_id=%s", state["project_id"])
        agent = RecommendationAgent(llm_service=llm_service)
        result = agent.recommend(
            comparison_result=state.get("comparison_result"),
            compliance_result=state.get("compliance_result"),
            human_feedback=state.get("human_feedback"),   # ← HITL feedback
        )

        if result.success:
            return {"recommendation_result": result.data, "errors": []}

        errors = [f"[RecommendationNode] {e}" for e in result.errors]
        logger.warning("[RecommendationNode] failed: %s", result.errors)
        return {"recommendation_result": None, "errors": errors}

    return recommendation_node


# ---------------------------------------------------------------------------
# Human Review Node
# ---------------------------------------------------------------------------

def make_human_review_node() -> Callable[[ProcurementState], dict]:
    """
    Factory: node that processes human reviewer feedback.

    Behaviour
    ---------
    * If no ``human_feedback`` is present in state → PENDING_REVIEW (workflow
      pauses naturally at END; human re-invokes with feedback populated).
    * If feedback is present AND ``feedback_processed`` is already True →
      the loop has run once; skip re-processing and return PENDING to END.
    * If feedback is present AND not yet processed → validate, produce
      HumanReviewResult, set ``feedback_processed=True`` if requires_rerun.

    The ``feedback_processed`` flag prevents the HumanReviewNode from
    re-processing the same feedback on the second pass through the loop,
    which would create an infinite cycle.
    """
    from app.human_review.schemas import HumanReviewResult, ReviewStatus
    from app.human_review.service import HumanReviewService

    _pending_result = HumanReviewResult(
        status=ReviewStatus.PENDING_REVIEW,
        approved=False,
        requires_rerun=False,
        feedback=None,
    )

    def human_review_node(state: ProcurementState) -> dict:
        logger.info(
            "[HumanReviewNode] project_id=%s  feedback_present=%s  feedback_processed=%s",
            state["project_id"],
            state.get("human_feedback") is not None,
            state.get("feedback_processed", False),
        )

        feedback = state.get("human_feedback")

        # No feedback submitted yet
        if feedback is None:
            return {"human_review_result": _pending_result, "errors": []}

        # Feedback already consumed on a prior loop iteration → just end
        if state.get("feedback_processed", False):
            logger.info("[HumanReviewNode] feedback already processed — ending loop")
            return {"human_review_result": _pending_result, "errors": []}

        try:
            svc = HumanReviewService()
            result = svc.process(feedback)
            logger.info("[HumanReviewNode] result=%s", result.status.value)

            update: dict = {"human_review_result": result, "errors": []}
            if result.requires_rerun:
                # Mark feedback consumed so the next pass through exits cleanly
                update["feedback_processed"] = True
            return update

        except ValueError as exc:
            logger.warning("[HumanReviewNode] validation error: %s", exc)
            return {
                "human_review_result": _pending_result,
                "errors": [f"[HumanReviewNode] {exc}"],
            }

    return human_review_node
