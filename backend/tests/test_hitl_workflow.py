"""
Comprehensive tests for Phase 3 Step 7: Human-in-the-Loop (HITL) Approval.

Covers:
  - HumanReviewService: all status paths + validation errors
  - Conditional LangGraph routing (_route_after_review)
  - RecommendationAgent with human_feedback
  - HumanReviewNode feedback_processed guard
  - Workflow termination scenarios
"""

import json
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.human_review.schemas import HumanFeedback, HumanReviewResult, ReviewStatus
from app.human_review.service import HumanReviewService
from app.schemas.comparison_schema import ComparisonResult, VendorComparison
from app.schemas.compliance_schema import (
    ComplianceResult,
    ComplianceStatus,
    QuotationCompliance,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PROJECT_ID = uuid.uuid4()


def make_feedback(
    status: ReviewStatus = ReviewStatus.APPROVED,
    selected_vendor: str | None = "Alpha",
    rejection_reason: str | None = None,
    reviewer_comments: str | None = None,
) -> HumanFeedback:
    return HumanFeedback(
        project_id=PROJECT_ID,
        recommended_vendor="Beta",
        selected_vendor=selected_vendor,
        status=status,
        reviewer_comments=reviewer_comments,
        rejection_reason=rejection_reason,
        review_timestamp=datetime.utcnow(),
    )


def _make_comparison(names: list[str]) -> ComparisonResult:
    vendors = [
        VendorComparison(vendor_name=n, grand_total=100_000.0 + i * 10_000,
                         discount=5_000.0, rank=i + 1)
        for i, n in enumerate(names)
    ]
    return ComparisonResult(
        lowest_price_vendor=names[0],
        lowest_price=100_000.0,
        currency_consistent=True,
        currency="INR",
        vendor_rankings=vendors,
    )


def _make_compliance(names: list[str], status: ComplianceStatus = ComplianceStatus.COMPLIANT) -> ComplianceResult:
    results = [
        QuotationCompliance(
            quotation_id=uuid.uuid4(),
            vendor_name=n,
            status=status,
            passed_checks=10,
            failed_checks=0,
            warning_count=0,
        )
        for n in names
    ]
    return ComplianceResult(
        project_id=PROJECT_ID,
        total_quotations=len(names),
        compliant_count=len(names) if status == ComplianceStatus.COMPLIANT else 0,
        partially_compliant_count=0,
        non_compliant_count=len(names) if status == ComplianceStatus.NON_COMPLIANT else 0,
        quotation_results=results,
    )


# ---------------------------------------------------------------------------
# HumanReviewService — status rules
# ---------------------------------------------------------------------------

class TestHumanReviewServiceApproved:

    def test_approved_approved_flag(self):
        svc = HumanReviewService()
        r = svc.process(make_feedback(ReviewStatus.APPROVED, selected_vendor="Alpha"))
        assert r.approved is True

    def test_approved_no_rerun(self):
        svc = HumanReviewService()
        r = svc.process(make_feedback(ReviewStatus.APPROVED, selected_vendor="Alpha"))
        assert r.requires_rerun is False

    def test_approved_status_preserved(self):
        svc = HumanReviewService()
        r = svc.process(make_feedback(ReviewStatus.APPROVED, selected_vendor="Alpha"))
        assert r.status == ReviewStatus.APPROVED

    def test_approved_feedback_attached(self):
        svc = HumanReviewService()
        fb = make_feedback(ReviewStatus.APPROVED, selected_vendor="Alpha")
        r = svc.process(fb)
        assert r.feedback is fb


class TestHumanReviewServiceRejected:

    def test_rejected_not_approved(self):
        svc = HumanReviewService()
        r = svc.process(make_feedback(ReviewStatus.REJECTED, selected_vendor=None,
                                      rejection_reason="Poor delivery record"))
        assert r.approved is False

    def test_rejected_requires_rerun(self):
        svc = HumanReviewService()
        r = svc.process(make_feedback(ReviewStatus.REJECTED, selected_vendor=None,
                                      rejection_reason="Poor delivery record"))
        assert r.requires_rerun is True

    def test_rejected_missing_reason_raises(self):
        svc = HumanReviewService()
        with pytest.raises(ValueError, match="rejection_reason"):
            svc.process(make_feedback(ReviewStatus.REJECTED, selected_vendor=None,
                                      rejection_reason=None))


class TestHumanReviewServiceRequiresChanges:

    def test_requires_changes_not_approved(self):
        svc = HumanReviewService()
        r = svc.process(make_feedback(ReviewStatus.REQUIRES_CHANGES, selected_vendor=None))
        assert r.approved is False

    def test_requires_changes_rerun(self):
        svc = HumanReviewService()
        r = svc.process(make_feedback(ReviewStatus.REQUIRES_CHANGES, selected_vendor=None))
        assert r.requires_rerun is True


class TestHumanReviewServicePending:

    def test_pending_not_approved(self):
        svc = HumanReviewService()
        r = svc.process(make_feedback(ReviewStatus.PENDING_REVIEW, selected_vendor=None))
        assert r.approved is False

    def test_pending_no_rerun(self):
        svc = HumanReviewService()
        r = svc.process(make_feedback(ReviewStatus.PENDING_REVIEW, selected_vendor=None))
        assert r.requires_rerun is False


class TestHumanReviewServiceValidation:

    def test_missing_selected_vendor_for_approved_raises(self):
        svc = HumanReviewService()
        with pytest.raises(ValueError, match="selected_vendor"):
            svc.process(make_feedback(ReviewStatus.APPROVED, selected_vendor=None))

    def test_empty_selected_vendor_raises(self):
        svc = HumanReviewService()
        with pytest.raises(ValueError, match="selected_vendor"):
            svc.process(make_feedback(ReviewStatus.APPROVED, selected_vendor=""))

    def test_missing_rejection_reason_raises(self):
        svc = HumanReviewService()
        with pytest.raises(ValueError, match="rejection_reason"):
            svc.process(make_feedback(ReviewStatus.REJECTED, selected_vendor=None,
                                      rejection_reason=None))

    def test_empty_rejection_reason_raises(self):
        svc = HumanReviewService()
        with pytest.raises(ValueError, match="rejection_reason"):
            svc.process(make_feedback(ReviewStatus.REJECTED, selected_vendor=None,
                                      rejection_reason=""))

    def test_requires_changes_no_mandatory_field(self):
        """REQUIRES_CHANGES has no mandatory extra fields."""
        svc = HumanReviewService()
        r = svc.process(make_feedback(ReviewStatus.REQUIRES_CHANGES, selected_vendor=None))
        assert r is not None


# ---------------------------------------------------------------------------
# Conditional routing function
# ---------------------------------------------------------------------------

class TestRouteAfterReview:

    def _make_state(self, review: HumanReviewResult | None, feedback_processed: bool = False) -> dict:
        return {"human_review_result": review, "feedback_processed": feedback_processed}

    def test_approved_routes_to_end(self):
        from app.graph.workflow import _route_after_review
        from langgraph.graph import END
        review = HumanReviewResult(status=ReviewStatus.APPROVED, approved=True,
                                   requires_rerun=False, feedback=None)
        assert _route_after_review(self._make_state(review)) == END

    def test_rejected_without_processed_routes_to_recommendation(self):
        from app.graph.workflow import _route_after_review
        review = HumanReviewResult(status=ReviewStatus.REJECTED, approved=False,
                                   requires_rerun=True, feedback=None)
        assert _route_after_review(self._make_state(review, feedback_processed=False)) == "recommendation"

    def test_rejected_with_processed_routes_to_end(self):
        """feedback_processed=True means loop already ran — route to END."""
        from app.graph.workflow import _route_after_review
        from langgraph.graph import END
        review = HumanReviewResult(status=ReviewStatus.REJECTED, approved=False,
                                   requires_rerun=True, feedback=None)
        assert _route_after_review(self._make_state(review, feedback_processed=True)) == END

    def test_requires_changes_routes_to_recommendation(self):
        from app.graph.workflow import _route_after_review
        review = HumanReviewResult(status=ReviewStatus.REQUIRES_CHANGES, approved=False,
                                   requires_rerun=True, feedback=None)
        assert _route_after_review(self._make_state(review)) == "recommendation"

    def test_pending_routes_to_end(self):
        from app.graph.workflow import _route_after_review
        from langgraph.graph import END
        review = HumanReviewResult(status=ReviewStatus.PENDING_REVIEW, approved=False,
                                   requires_rerun=False, feedback=None)
        assert _route_after_review(self._make_state(review)) == END

    def test_no_review_result_routes_to_end(self):
        from app.graph.workflow import _route_after_review
        from langgraph.graph import END
        assert _route_after_review(self._make_state(None)) == END


# ---------------------------------------------------------------------------
# RecommendationAgent with HumanFeedback
# ---------------------------------------------------------------------------

class TestRecommendationAgentWithFeedback:

    def _make_setup(self):
        comp  = _make_comparison(["Alpha", "Beta"])
        compl = _make_compliance(["Alpha", "Beta"])
        return comp, compl

    def test_feedback_does_not_change_deterministic_winner(self):
        """Without LLM, feedback doesn't alter the deterministic selection."""
        from app.agents.recommendation_agent import RecommendationAgent
        comp, compl = self._make_setup()
        fb = make_feedback(ReviewStatus.REJECTED, selected_vendor=None,
                           rejection_reason="Too expensive")

        result = RecommendationAgent().recommend(comp, compl, human_feedback=fb)
        assert result.success is True
        assert result.data.recommended_vendor == "Alpha"

    def test_feedback_injected_into_llm_prompt(self):
        """Verify the LLM prompt contains reviewer comments when feedback given."""
        from app.agents.recommendation_agent import _build_reasoning_user_prompt

        comp, compl = self._make_setup()
        fb = make_feedback(ReviewStatus.REJECTED, selected_vendor=None,
                           rejection_reason="Unreliable vendor",
                           reviewer_comments="Choose Beta instead")

        prompt = _build_reasoning_user_prompt("Alpha", comp, compl, ["Beta"], human_feedback=fb)
        assert "REVIEWER FEEDBACK" in prompt
        assert "Unreliable vendor" in prompt
        assert "Choose Beta instead" in prompt
        assert "NON_COMPLIANT" in prompt or "NEVER recommend" in prompt

    def test_no_feedback_prompt_omits_reviewer_section(self):
        from app.agents.recommendation_agent import _build_reasoning_user_prompt
        comp, compl = self._make_setup()
        prompt = _build_reasoning_user_prompt("Alpha", comp, compl, ["Beta"], human_feedback=None)
        assert "REVIEWER FEEDBACK" not in prompt

    def test_feedback_reaches_llm_service(self):
        """Verify that when feedback is present, LLM is called with it in prompt."""
        from app.agents.recommendation_agent import RecommendationAgent
        from app.services.llm_service import LLMService

        comp, compl = self._make_setup()
        fb = make_feedback(ReviewStatus.REJECTED, selected_vendor=None,
                           rejection_reason="Too slow")

        mock_llm = MagicMock(spec=LLMService)
        mock_llm.complete_json.return_value = json.dumps({
            "reasoning": "Alpha remains best despite rejection.",
            "strengths": ["Lowest price"],
            "risks": [],
            "alternatives": [],
        })

        result = RecommendationAgent(llm_service=mock_llm).recommend(comp, compl, human_feedback=fb)
        assert result.success is True

        # Check that the LLM was called and prompt contained feedback
        call_kwargs = mock_llm.complete_json.call_args
        user_content = call_kwargs.kwargs.get("user_content", "")
        assert "Too slow" in user_content


# ---------------------------------------------------------------------------
# HumanReviewNode — feedback_processed guard
# ---------------------------------------------------------------------------

class TestHumanReviewNodeGuard:

    def _make_state(self, feedback, feedback_processed: bool = False) -> dict:
        return {
            "project_id": PROJECT_ID,
            "human_feedback": feedback,
            "feedback_processed": feedback_processed,
            "errors": [],
        }

    def test_no_feedback_returns_pending(self):
        from app.graph.nodes import make_human_review_node
        node = make_human_review_node()
        result = node(self._make_state(None))
        assert result["human_review_result"].status == ReviewStatus.PENDING_REVIEW

    def test_valid_rejection_sets_feedback_processed(self):
        from app.graph.nodes import make_human_review_node
        node = make_human_review_node()
        fb = make_feedback(ReviewStatus.REJECTED, selected_vendor=None,
                           rejection_reason="Poor quality")
        result = node(self._make_state(fb, feedback_processed=False))
        assert result.get("feedback_processed") is True

    def test_already_processed_returns_pending(self):
        """When feedback_processed=True, node skips and returns PENDING → ends loop."""
        from app.graph.nodes import make_human_review_node
        node = make_human_review_node()
        fb = make_feedback(ReviewStatus.REJECTED, selected_vendor=None,
                           rejection_reason="Poor quality")
        result = node(self._make_state(fb, feedback_processed=True))
        assert result["human_review_result"].status == ReviewStatus.PENDING_REVIEW

    def test_invalid_feedback_adds_error(self):
        """Missing rejection_reason → validation error → error state, no crash."""
        from app.graph.nodes import make_human_review_node
        node = make_human_review_node()
        fb = make_feedback(ReviewStatus.REJECTED, selected_vendor=None, rejection_reason=None)
        result = node(self._make_state(fb))
        assert len(result["errors"]) > 0
        assert "HumanReviewNode" in result["errors"][0]


# ---------------------------------------------------------------------------
# Workflow build + termination
# ---------------------------------------------------------------------------

class TestWorkflowTermination:

    def test_workflow_builds_with_hitl_node(self):
        from app.graph.workflow import build_workflow
        db = MagicMock()
        wf = build_workflow(db, llm_service=None)
        assert wf is not None

    def test_approved_workflow_terminates(self):
        """When APPROVED feedback provided, workflow runs through and terminates."""
        from app.agents.comparison_agent import ComparisonAgent, ComparisonAgentResult
        from app.agents.compliance_agent import ComplianceAgent, ComplianceAgentResult
        from app.graph.workflow import run_procurement_workflow

        comp_data  = _make_comparison(["Alpha"])
        compl_data = _make_compliance(["Alpha"])
        fb = make_feedback(ReviewStatus.APPROVED, selected_vendor="Alpha")

        mock_comp  = ComparisonAgentResult(success=True, data=comp_data, project_id=PROJECT_ID)
        mock_compl = ComplianceAgentResult(success=True, data=compl_data)

        with patch.object(ComparisonAgent, "compare", return_value=mock_comp), \
             patch.object(ComplianceAgent, "evaluate", return_value=mock_compl):
            state = run_procurement_workflow(PROJECT_ID, MagicMock(), human_feedback=fb)

        assert state["human_review_result"].approved is True
        assert state["human_review_result"].requires_rerun is False
