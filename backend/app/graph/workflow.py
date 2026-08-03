"""
LangGraph workflow definition for ProcureAI procurement analysis.

Full pipeline with Human-in-the-Loop (HITL) review:

  START → Comparison → Compliance → Recommendation → Human Review
                                          ↑                  |
                                          └── requires_rerun ┘
                                                  |
                                                 END

``feedback_processed`` in state ensures the loop runs at most once per
human feedback submission, preventing infinite recursion.

Usage::

    from app.graph.workflow import run_procurement_workflow

    # First pass — no human feedback yet
    state = run_procurement_workflow(project_id, db, llm_service)
    # state["human_review_result"].status == PENDING_REVIEW

    # Second pass — reviewer rejects the recommendation
    state = run_procurement_workflow(
        project_id, db, llm_service,
        human_feedback=HumanFeedback(status=REJECTED, rejection_reason="...")
    )
    # state["human_review_result"].status == REJECTED
    # state["recommendation_result"] updated with reviewer feedback
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.graph.nodes import (
    make_comparison_node,
    make_compliance_node,
    make_human_review_node,
    make_recommendation_node,
)
from app.graph.state import ProcurementState
from app.human_review.schemas import HumanFeedback
from app.services.llm_service import LLMService

logger = get_logger(__name__)

# Maximum graph iterations (prevents runaway loops in edge cases)
_RECURSION_LIMIT = 10


# ---------------------------------------------------------------------------
# Routing function
# ---------------------------------------------------------------------------

def _route_after_review(state: ProcurementState) -> str:
    """
    Conditional routing function after Human Review node.

    Returns
    -------
    "recommendation" : if the reviewer rejected/required changes AND the
                       feedback has NOT yet been consumed (loop allowed).
    "__end__"        : otherwise (approved, pending, or loop exhausted).
    """
    from langgraph.graph import END

    review = state.get("human_review_result")
    if review and review.requires_rerun and not state.get("feedback_processed", False):
        logger.info("[Workflow] routing back to recommendation node")
        return "recommendation"

    logger.info("[Workflow] routing to END")
    return END


# ---------------------------------------------------------------------------
# Workflow builder
# ---------------------------------------------------------------------------

def build_workflow(
    db: Session,
    llm_service: Optional[LLMService] = None,
):
    """
    Construct and compile the ProcureAI LangGraph workflow.

    Args:
        db:          Active SQLAlchemy session (passed to DB-bound nodes).
        llm_service: Optional Mistral client for summary generation.

    Returns:
        A compiled LangGraph ``CompiledStateGraph``.
    """
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise RuntimeError(
            "langgraph is not installed. Run: pip install langgraph"
        ) from exc

    graph: StateGraph = StateGraph(ProcurementState)

    # ── Register nodes ────────────────────────────────────────────────────
    graph.add_node("comparison",    make_comparison_node(db, llm_service))
    graph.add_node("compliance",    make_compliance_node(db, llm_service))
    graph.add_node("recommendation", make_recommendation_node(llm_service))
    graph.add_node("human_review",  make_human_review_node())

    # ── Linear edges ──────────────────────────────────────────────────────
    graph.add_edge(START,            "comparison")
    graph.add_edge("comparison",     "compliance")
    graph.add_edge("compliance",     "recommendation")
    graph.add_edge("recommendation", "human_review")

    # ── Conditional edge after Human Review ───────────────────────────────
    graph.add_conditional_edges(
        "human_review",
        _route_after_review,
        {"recommendation": "recommendation", END: END},
    )

    return graph.compile()


# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------

def run_procurement_workflow(
    project_id: uuid.UUID,
    db: Session,
    llm_service: Optional[LLMService] = None,
    human_feedback: Optional[HumanFeedback] = None,
) -> ProcurementState:
    """
    Build, compile, and execute the full procurement workflow.

    Args:
        project_id:     UUID of the ProcurementProject to analyse.
        db:             Active SQLAlchemy session.
        llm_service:    Optional Mistral client.
        human_feedback: Reviewer's HumanFeedback (None on first invocation).

    Returns:
        Final ``ProcurementState`` after all nodes have run.
    """
    logger.info(
        "Starting procurement workflow  project_id=%s  feedback=%s",
        project_id,
        human_feedback.status.value if human_feedback else "none",
    )

    compiled = build_workflow(db, llm_service)

    initial_state: ProcurementState = {
        "project_id":             project_id,
        "comparison_result":      None,
        "compliance_result":      None,
        "recommendation_result":  None,
        "human_review_result":    None,
        "human_feedback":         human_feedback,
        "feedback_processed":     False,
        "errors":                 [],
    }

    final_state: ProcurementState = compiled.invoke(
        initial_state,
        config={"recursion_limit": _RECURSION_LIMIT},
    )

    logger.info(
        "Workflow complete  errors=%d  review_status=%s",
        len(final_state.get("errors", [])),
        final_state.get("human_review_result", {}).status.value
        if final_state.get("human_review_result")
        else "none",
    )
    return final_state
