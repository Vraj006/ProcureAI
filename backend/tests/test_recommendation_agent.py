"""
Unit tests for RecommendationAgent and LangGraph workflow.

All LLM calls and DB-bound agents are mocked.
Tests cover all required scenarios:
  - single compliant vendor
  - multiple compliant vendors (lowest price wins)
  - no compliant vendors
  - LLM failure → deterministic fallback
  - workflow execution (state propagation through graph)
"""

import json
import uuid
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.comparison_schema import ComparisonResult, VendorComparison
from app.schemas.compliance_schema import (
    ComplianceResult,
    ComplianceStatus,
    QuotationCompliance,
)
from app.schemas.recommendation_schema import RecommendationResult


# ---------------------------------------------------------------------------
# Helpers — build lightweight result stubs
# ---------------------------------------------------------------------------

def make_vendor_comparison(
    name: str,
    rank: int,
    grand_total: float = 100_000.0,
    discount: float = 5_000.0,
    delivery_time: str = "4 weeks",
    warranty: str = "1 year",
) -> VendorComparison:
    return VendorComparison(
        vendor_name=name,
        grand_total=grand_total,
        discount=discount,
        delivery_time=delivery_time,
        warranty=warranty,
        rank=rank,
    )


def make_quotation_compliance(
    vendor_name: str,
    status: ComplianceStatus,
    quotation_id: uuid.UUID | None = None,
) -> QuotationCompliance:
    return QuotationCompliance(
        quotation_id=quotation_id or uuid.uuid4(),
        vendor_name=vendor_name,
        status=status,
        passed_checks=10,
        failed_checks=1 if status == ComplianceStatus.NON_COMPLIANT else 0,
        warning_count=1 if status == ComplianceStatus.PARTIALLY_COMPLIANT else 0,
        issues=[],
    )


def make_comparison(vendors: list[VendorComparison], **kwargs) -> ComparisonResult:
    return ComparisonResult(
        lowest_price_vendor=vendors[0].vendor_name if vendors else None,
        lowest_price=vendors[0].grand_total if vendors else None,
        highest_discount_vendor=vendors[0].vendor_name if vendors else None,
        fastest_delivery_vendor=vendors[0].vendor_name if vendors else None,
        best_warranty_vendor=vendors[0].vendor_name if vendors else None,
        currency_consistent=True,
        currency="INR",
        vendor_rankings=vendors,
        **kwargs,
    )


def make_compliance(quotation_compliances: list[QuotationCompliance]) -> ComplianceResult:
    compliant   = sum(1 for q in quotation_compliances if q.status == ComplianceStatus.COMPLIANT)
    partial     = sum(1 for q in quotation_compliances if q.status == ComplianceStatus.PARTIALLY_COMPLIANT)
    noncompliant = sum(1 for q in quotation_compliances if q.status == ComplianceStatus.NON_COMPLIANT)
    return ComplianceResult(
        project_id=uuid.uuid4(),
        total_quotations=len(quotation_compliances),
        compliant_count=compliant,
        partially_compliant_count=partial,
        non_compliant_count=noncompliant,
        quotation_results=quotation_compliances,
    )


LLM_REASONING_RESPONSE = json.dumps({
    "reasoning": "Vendor Alpha offers the lowest price with full compliance.",
    "strengths": ["Lowest price", "Full compliance"],
    "risks": ["Single vendor risk"],
    "alternatives": [],
})


# ---------------------------------------------------------------------------
# RecommendationAgent — core scenarios
# ---------------------------------------------------------------------------

class TestSingleCompliantVendor:

    def test_returns_success(self):
        from app.agents.recommendation_agent import RecommendationAgent
        comp  = make_comparison([make_vendor_comparison("Alpha", rank=1)])
        compl = make_compliance([make_quotation_compliance("Alpha", ComplianceStatus.COMPLIANT)])

        result = RecommendationAgent().recommend(comp, compl)
        assert result.success is True

    def test_recommends_the_only_vendor(self):
        from app.agents.recommendation_agent import RecommendationAgent
        comp  = make_comparison([make_vendor_comparison("Alpha", rank=1)])
        compl = make_compliance([make_quotation_compliance("Alpha", ComplianceStatus.COMPLIANT)])

        result = RecommendationAgent().recommend(comp, compl)
        assert result.data.recommended_vendor == "Alpha"

    def test_confidence_is_nonzero(self):
        from app.agents.recommendation_agent import RecommendationAgent
        comp  = make_comparison([make_vendor_comparison("Alpha", rank=1)])
        compl = make_compliance([make_quotation_compliance("Alpha", ComplianceStatus.COMPLIANT)])

        result = RecommendationAgent().recommend(comp, compl)
        assert result.data.confidence_score > 0
        assert result.data.confidence_score <= 100

    def test_no_recommendation_flag_false(self):
        from app.agents.recommendation_agent import RecommendationAgent
        comp  = make_comparison([make_vendor_comparison("Alpha", rank=1)])
        compl = make_compliance([make_quotation_compliance("Alpha", ComplianceStatus.COMPLIANT)])

        result = RecommendationAgent().recommend(comp, compl)
        assert result.data.is_no_recommendation is False


class TestMultipleCompliantVendors:

    def test_recommends_lowest_price(self):
        """Alpha is rank 1 (cheapest) among compliant vendors."""
        from app.agents.recommendation_agent import RecommendationAgent
        vendors = [
            make_vendor_comparison("Alpha", rank=1, grand_total=80_000),
            make_vendor_comparison("Beta",  rank=2, grand_total=100_000),
            make_vendor_comparison("Gamma", rank=3, grand_total=120_000),
        ]
        comp  = make_comparison(vendors)
        compl = make_compliance([
            make_quotation_compliance("Alpha", ComplianceStatus.COMPLIANT),
            make_quotation_compliance("Beta",  ComplianceStatus.COMPLIANT),
            make_quotation_compliance("Gamma", ComplianceStatus.PARTIALLY_COMPLIANT),
        ])

        result = RecommendationAgent().recommend(comp, compl)
        assert result.data.recommended_vendor == "Alpha"

    def test_alternatives_list_populated(self):
        from app.agents.recommendation_agent import RecommendationAgent
        vendors = [
            make_vendor_comparison("Alpha", rank=1, grand_total=80_000),
            make_vendor_comparison("Beta",  rank=2, grand_total=100_000),
        ]
        comp  = make_comparison(vendors)
        compl = make_compliance([
            make_quotation_compliance("Alpha", ComplianceStatus.COMPLIANT),
            make_quotation_compliance("Beta",  ComplianceStatus.COMPLIANT),
        ])

        result = RecommendationAgent().recommend(comp, compl)
        # When LLM is absent, alternatives comes from deterministic list
        assert "Beta" in result.data.alternatives

    def test_skips_non_compliant_rank_1(self):
        """Beta is rank 2 but Alpha is NON_COMPLIANT — Beta should win."""
        from app.agents.recommendation_agent import RecommendationAgent
        vendors = [
            make_vendor_comparison("Alpha", rank=1, grand_total=70_000),
            make_vendor_comparison("Beta",  rank=2, grand_total=90_000),
        ]
        comp  = make_comparison(vendors)
        compl = make_compliance([
            make_quotation_compliance("Alpha", ComplianceStatus.NON_COMPLIANT),
            make_quotation_compliance("Beta",  ComplianceStatus.COMPLIANT),
        ])

        result = RecommendationAgent().recommend(comp, compl)
        assert result.data.recommended_vendor == "Beta"

    def test_partially_compliant_vendor_is_eligible(self):
        """PARTIALLY_COMPLIANT vendors ARE eligible — only NON_COMPLIANT are excluded."""
        from app.agents.recommendation_agent import RecommendationAgent
        vendors = [make_vendor_comparison("Gamma", rank=1)]
        comp  = make_comparison(vendors)
        compl = make_compliance([
            make_quotation_compliance("Gamma", ComplianceStatus.PARTIALLY_COMPLIANT),
        ])

        result = RecommendationAgent().recommend(comp, compl)
        assert result.data.recommended_vendor == "Gamma"
        assert result.data.is_no_recommendation is False


class TestNoCompliantVendor:

    def test_returns_no_recommendation(self):
        from app.agents.recommendation_agent import RecommendationAgent
        vendors = [
            make_vendor_comparison("Alpha", rank=1),
            make_vendor_comparison("Beta",  rank=2),
        ]
        comp  = make_comparison(vendors)
        compl = make_compliance([
            make_quotation_compliance("Alpha", ComplianceStatus.NON_COMPLIANT),
            make_quotation_compliance("Beta",  ComplianceStatus.NON_COMPLIANT),
        ])

        result = RecommendationAgent().recommend(comp, compl)
        assert result.success is True
        assert result.data.is_no_recommendation is True
        assert result.data.recommended_vendor is None
        assert result.data.confidence_score == 0

    def test_missing_upstream_results_returns_error(self):
        from app.agents.recommendation_agent import RecommendationAgent
        result = RecommendationAgent().recommend(None, None)
        assert result.success is False
        assert len(result.errors) > 0


class TestLLMIntegration:

    def _make_mock_llm(self, response: str):
        from app.services.llm_service import LLMService
        mock = MagicMock(spec=LLMService)
        mock.complete_json.return_value = response
        return mock

    def test_llm_reasoning_applied(self):
        from app.agents.recommendation_agent import RecommendationAgent
        comp  = make_comparison([make_vendor_comparison("Alpha", rank=1)])
        compl = make_compliance([make_quotation_compliance("Alpha", ComplianceStatus.COMPLIANT)])

        agent  = RecommendationAgent(llm_service=self._make_mock_llm(LLM_REASONING_RESPONSE))
        result = agent.recommend(comp, compl)

        assert result.data.reasoning is not None
        assert "Alpha" in result.data.reasoning or len(result.data.reasoning) > 0
        assert isinstance(result.data.strengths, list)
        assert isinstance(result.data.risks, list)
        assert result.data.is_deterministic_fallback is False

    def test_llm_failure_deterministic_fallback(self):
        from app.agents.recommendation_agent import RecommendationAgent
        from app.services.llm_service import LLMService

        mock_llm = MagicMock(spec=LLMService)
        mock_llm.complete_json.side_effect = RuntimeError("Mistral API timeout")

        comp  = make_comparison([make_vendor_comparison("Alpha", rank=1)])
        compl = make_compliance([make_quotation_compliance("Alpha", ComplianceStatus.COMPLIANT)])

        agent  = RecommendationAgent(llm_service=mock_llm)
        result = agent.recommend(comp, compl)

        assert result.success is True
        assert result.data.recommended_vendor == "Alpha"   # deterministic still works
        assert result.data.reasoning is None               # LLM part missing
        assert result.data.is_deterministic_fallback is True


class TestConfidenceScore:

    def test_compliant_vendor_higher_confidence_than_partial(self):
        from app.agents.recommendation_agent import RecommendationAgent

        compliant_comp  = make_comparison([make_vendor_comparison("A", rank=1)])
        compliant_compl = make_compliance([make_quotation_compliance("A", ComplianceStatus.COMPLIANT)])

        partial_comp  = make_comparison([make_vendor_comparison("B", rank=1)])
        partial_compl = make_compliance([make_quotation_compliance("B", ComplianceStatus.PARTIALLY_COMPLIANT)])

        compliant_result = RecommendationAgent().recommend(compliant_comp, compliant_compl)
        partial_result   = RecommendationAgent().recommend(partial_comp, partial_compl)

        assert compliant_result.data.confidence_score > partial_result.data.confidence_score

    def test_confidence_within_bounds(self):
        from app.agents.recommendation_agent import RecommendationAgent
        comp  = make_comparison([make_vendor_comparison("A", rank=1)])
        compl = make_compliance([make_quotation_compliance("A", ComplianceStatus.COMPLIANT)])

        result = RecommendationAgent().recommend(comp, compl)
        assert 0 <= result.data.confidence_score <= 100


# ---------------------------------------------------------------------------
# LangGraph workflow — state propagation tests
# ---------------------------------------------------------------------------

class TestWorkflowExecution:
    """
    Tests the compiled workflow by mocking agent calls at the node level.
    Uses patch to intercept agent instantiation inside nodes.
    """

    def _make_db(self) -> MagicMock:
        return MagicMock()

    def test_workflow_builds_without_error(self):
        from app.graph.workflow import build_workflow
        db = self._make_db()
        workflow = build_workflow(db, llm_service=None)
        assert workflow is not None

    def test_workflow_propagates_comparison_result(self):
        from app.agents.comparison_agent import ComparisonAgent, ComparisonAgentResult
        from app.graph.workflow import run_procurement_workflow

        project_id = uuid.uuid4()
        db = self._make_db()

        comp_result = make_comparison([make_vendor_comparison("Alpha", rank=1)])
        compl_result = make_compliance([make_quotation_compliance("Alpha", ComplianceStatus.COMPLIANT)])

        mock_comp_result  = ComparisonAgentResult(success=True, data=comp_result, project_id=project_id)
        mock_compl_result = MagicMock()
        mock_compl_result.success = True
        mock_compl_result.data = compl_result

        with patch.object(ComparisonAgent, "compare", return_value=mock_comp_result):
            from app.agents.compliance_agent import ComplianceAgent
            with patch.object(ComplianceAgent, "evaluate", return_value=mock_compl_result):
                final_state = run_procurement_workflow(project_id, db, llm_service=None)

        assert final_state["comparison_result"] is comp_result
        assert final_state["compliance_result"] is compl_result

    def test_workflow_errors_accumulate(self):
        from app.agents.comparison_agent import ComparisonAgent, ComparisonAgentResult
        from app.graph.workflow import run_procurement_workflow

        project_id = uuid.uuid4()
        db = self._make_db()

        # Comparison fails
        fail_result = ComparisonAgentResult(
            success=False,
            errors=["Not enough quotations."],
            project_id=project_id,
        )

        mock_compl_result = MagicMock()
        mock_compl_result.success = True
        mock_compl_result.data = make_compliance([])

        with patch.object(ComparisonAgent, "compare", return_value=fail_result):
            from app.agents.compliance_agent import ComplianceAgent
            with patch.object(ComplianceAgent, "evaluate", return_value=mock_compl_result):
                final_state = run_procurement_workflow(project_id, db, llm_service=None)

        # Errors from comparison node should be in state
        assert any("Not enough" in e or "ComparisonNode" in e for e in final_state["errors"])
