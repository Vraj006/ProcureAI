"""
Unit tests for ComparisonService (pure logic, no DB, no LLM).

ComparisonService is tested in isolation by constructing lightweight
ExtractedQuotation ORM instances directly — no real DB session needed.
The ComparisonAgent is tested with a mocked repository.
"""

import uuid
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.models.extracted_quotation import ExtractedQuotation, ExtractionStatus
from app.schemas.comparison_schema import ComparisonAgentResult
from app.services.comparison_service import (
    ComparisonService,
    _parse_delivery_days,
    _parse_warranty_months,
)


# ---------------------------------------------------------------------------
# Helpers — build lightweight ExtractedQuotation stubs (no DB needed)
# ---------------------------------------------------------------------------

def make_eq(
    *,
    vendor_name: str = "Vendor",
    grand_total=None,
    discount=None,
    currency: str = "USD",
    delivery_time: str | None = None,
    warranty: str | None = None,
) -> ExtractedQuotation:
    eq = ExtractedQuotation()
    eq.id = uuid.uuid4()
    eq.quotation_id = uuid.uuid4()
    eq.vendor_name = vendor_name
    eq.grand_total = Decimal(str(grand_total)) if grand_total is not None else None
    eq.discount = Decimal(str(discount)) if discount is not None else None
    eq.currency = currency
    eq.delivery_time = delivery_time
    eq.warranty = warranty
    eq.extraction_status = ExtractionStatus.SUCCESS
    return eq


# ---------------------------------------------------------------------------
# Parsing utils
# ---------------------------------------------------------------------------

class TestParseDeliveryDays:
    def test_weeks(self):          assert _parse_delivery_days("4 weeks") == 28
    def test_days(self):           assert _parse_delivery_days("30 days") == 30
    def test_month(self):          assert _parse_delivery_days("1 month") == 30
    def test_year(self):           assert _parse_delivery_days("1 year") == 365
    def test_fractional(self):     assert _parse_delivery_days("1.5 weeks") == 10
    def test_ambiguous(self):      assert _parse_delivery_days("ASAP") is None
    def test_empty(self):          assert _parse_delivery_days("") is None
    def test_none_input(self):     assert _parse_delivery_days(None) is None  # type: ignore[arg-type]
    def test_case_insensitive(self): assert _parse_delivery_days("2 WEEKS") == 14


class TestParseWarrantyMonths:
    def test_months(self):         assert _parse_warranty_months("12 months") == 12
    def test_years(self):          assert _parse_warranty_months("2 years") == 24
    def test_one_year(self):       assert _parse_warranty_months("1 year") == 12
    def test_ambiguous(self):      assert _parse_warranty_months("lifetime") is None
    def test_empty(self):          assert _parse_warranty_months("") is None


# ---------------------------------------------------------------------------
# ComparisonService — success scenarios
# ---------------------------------------------------------------------------

class TestComparisonServiceWinners:

    def setup_method(self):
        self.service = ComparisonService()
        self.vendors = [
            make_eq(vendor_name="Alpha",   grand_total=100_000, discount=5_000,  delivery_time="4 weeks",  warranty="1 year",   currency="INR"),
            make_eq(vendor_name="Beta",    grand_total=90_000,  discount=10_000, delivery_time="2 weeks",  warranty="2 years",  currency="INR"),
            make_eq(vendor_name="Gamma",   grand_total=110_000, discount=2_000,  delivery_time="6 weeks",  warranty="6 months", currency="INR"),
        ]

    def test_lowest_price_vendor(self):
        result = self.service.compare(self.vendors)
        assert result.lowest_price_vendor == "Beta"
        assert result.lowest_price == 90_000.0

    def test_highest_discount_vendor(self):
        result = self.service.compare(self.vendors)
        assert result.highest_discount_vendor == "Beta"

    def test_fastest_delivery_vendor(self):
        result = self.service.compare(self.vendors)
        assert result.fastest_delivery_vendor == "Beta"  # 2 weeks = 14 days

    def test_best_warranty_vendor(self):
        result = self.service.compare(self.vendors)
        assert result.best_warranty_vendor == "Beta"  # 2 years = 24 months

    def test_vendor_rankings_ordered_by_price(self):
        result = self.service.compare(self.vendors)
        names = [v.vendor_name for v in result.vendor_rankings]
        assert names == ["Beta", "Alpha", "Gamma"]

    def test_ranks_are_sequential(self):
        result = self.service.compare(self.vendors)
        ranks = [v.rank for v in result.vendor_rankings]
        assert ranks == [1, 2, 3]

    def test_currency_consistent(self):
        result = self.service.compare(self.vendors)
        assert result.currency_consistent is True
        assert result.currency == "INR"


class TestComparisonServiceEdgeCases:

    def setup_method(self):
        self.service = ComparisonService()

    def test_currency_inconsistency_detected(self):
        vendors = [
            make_eq(vendor_name="A", grand_total=100, currency="USD"),
            make_eq(vendor_name="B", grand_total=200, currency="EUR"),
        ]
        result = self.service.compare(vendors)
        assert result.currency_consistent is False
        assert result.currency is None

    def test_null_grand_total_excluded_from_ranking(self):
        vendors = [
            make_eq(vendor_name="WithTotal",    grand_total=50_000, currency="USD"),
            make_eq(vendor_name="WithoutTotal", grand_total=None,   currency="USD"),
        ]
        result = self.service.compare(vendors)
        ranked = [v for v in result.vendor_rankings if v.grand_total is not None]
        assert len(ranked) == 1
        assert ranked[0].vendor_name == "WithTotal"
        assert ranked[0].rank == 1

    def test_all_null_grand_totals(self):
        vendors = [
            make_eq(vendor_name="A", grand_total=None, currency="USD"),
            make_eq(vendor_name="B", grand_total=None, currency="USD"),
        ]
        result = self.service.compare(vendors)
        assert result.lowest_price_vendor is None
        assert result.lowest_price is None
        assert len(result.vendor_rankings) == 2

    def test_ambiguous_delivery_skipped(self):
        vendors = [
            make_eq(vendor_name="A", grand_total=100, delivery_time="ASAP"),
            make_eq(vendor_name="B", grand_total=200, delivery_time="Upon approval"),
        ]
        result = self.service.compare(vendors)
        assert result.fastest_delivery_vendor is None

    def test_ambiguous_warranty_skipped(self):
        vendors = [
            make_eq(vendor_name="A", warranty="Lifetime guarantee"),
            make_eq(vendor_name="B", warranty="As per standard"),
        ]
        result = self.service.compare(vendors)
        assert result.best_warranty_vendor is None

    def test_no_discount_data(self):
        vendors = [
            make_eq(vendor_name="A", grand_total=100, discount=None, currency="USD"),
            make_eq(vendor_name="B", grand_total=200, discount=None, currency="USD"),
        ]
        result = self.service.compare(vendors)
        assert result.highest_discount_vendor is None


# ---------------------------------------------------------------------------
# ComparisonAgent (mocked repository)
# ---------------------------------------------------------------------------

class TestComparisonAgentMinimumQuotations:

    def test_zero_quotations_returns_error(self):
        from app.agents.comparison_agent import ComparisonAgent
        db = MagicMock()
        agent = ComparisonAgent(db=db, generate_summary=False)
        with patch.object(agent._repo, "get_by_project_id", return_value=[]):
            result = agent.compare(uuid.uuid4())
        assert result.success is False
        assert "2" in result.errors[0]

    def test_one_quotation_returns_error(self):
        from app.agents.comparison_agent import ComparisonAgent
        db = MagicMock()
        agent = ComparisonAgent(db=db, generate_summary=False)
        with patch.object(agent._repo, "get_by_project_id", return_value=[make_eq()]):
            result = agent.compare(uuid.uuid4())
        assert result.success is False

    def test_two_quotations_returns_success(self):
        from app.agents.comparison_agent import ComparisonAgent
        db = MagicMock()
        agent = ComparisonAgent(db=db, generate_summary=False)
        vendors = [
            make_eq(vendor_name="A", grand_total=100, currency="USD"),
            make_eq(vendor_name="B", grand_total=200, currency="USD"),
        ]
        with patch.object(agent._repo, "get_by_project_id", return_value=vendors):
            result = agent.compare(uuid.uuid4())
        assert result.success is True
        assert result.data is not None
        assert result.data.lowest_price_vendor == "A"

    def test_db_error_returns_structured_failure(self):
        from app.agents.comparison_agent import ComparisonAgent
        db = MagicMock()
        agent = ComparisonAgent(db=db, generate_summary=False)
        with patch.object(agent._repo, "get_by_project_id", side_effect=RuntimeError("DB down")):
            result = agent.compare(uuid.uuid4())
        assert result.success is False
        assert "Database error" in result.errors[0]
