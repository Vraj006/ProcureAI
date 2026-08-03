"""
Unit tests for ComplianceService and ComplianceAgent.

ComplianceService is tested with lightweight ExtractedQuotation stubs
(no real DB session). ComplianceAgent is tested with a mocked repository.
Covers all 20+ required test scenarios.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

import app.services.compliance_service as compliance_module
from app.models.extracted_quotation import (
    ExtractedQuotation,
    ExtractedQuotationItem,
    ExtractionStatus,
)
from app.schemas.compliance_schema import ComplianceStatus, Severity
from app.services.compliance_service import ComplianceService


# ---------------------------------------------------------------------------
# Constants for dates
# ---------------------------------------------------------------------------

TODAY = date.today()
PAST_DATE  = (TODAY - timedelta(days=30)).isoformat()   # 30 days ago
FUTURE_DATE = (TODAY + timedelta(days=30)).isoformat()   # 30 days from today
FAR_FUTURE  = (TODAY + timedelta(days=365)).isoformat()   # 1 year from today


# ---------------------------------------------------------------------------
# Stub builders
# ---------------------------------------------------------------------------

def make_eq(**kwargs) -> ExtractedQuotation:
    """Build a minimal ExtractedQuotation with sensible defaults."""
    eq = ExtractedQuotation()
    eq.id               = uuid.uuid4()
    eq.quotation_id     = uuid.uuid4()
    eq.vendor_name      = kwargs.get("vendor_name",     "Acme Ltd")
    eq.vendor_gst_number = kwargs.get("vendor_gst_number", "27ABCDE1234F1Z5")
    eq.quotation_number = kwargs.get("quotation_number", "Q-001")
    eq.quotation_date   = kwargs.get("quotation_date",  PAST_DATE)
    eq.currency         = kwargs.get("currency",        "INR")
    eq.grand_total      = kwargs.get("grand_total",     Decimal("100000"))
    eq.subtotal         = kwargs.get("subtotal",        Decimal("90000"))
    eq.discount         = kwargs.get("discount",        Decimal("5000"))
    eq.tax              = kwargs.get("tax",             Decimal("15000"))
    eq.shipping_cost    = kwargs.get("shipping_cost",   Decimal("500"))
    eq.payment_terms    = kwargs.get("payment_terms",   "Net 30")
    eq.delivery_time    = kwargs.get("delivery_time",   "4 weeks")
    eq.warranty         = kwargs.get("warranty",        "1 year")
    eq.valid_until      = kwargs.get("valid_until",     FAR_FUTURE)
    eq.extraction_status = ExtractionStatus.SUCCESS
    return eq


def make_item(**kwargs) -> ExtractedQuotationItem:
    item = ExtractedQuotationItem()
    item.id                      = uuid.uuid4()
    item.extracted_quotation_id  = uuid.uuid4()
    item.item_name   = kwargs.get("item_name",   "Industrial Pump")
    item.quantity    = kwargs.get("quantity",    Decimal("5"))
    item.unit_price  = kwargs.get("unit_price",  Decimal("20000"))
    item.total_price = kwargs.get("total_price", Decimal("100000"))
    return item


# ---------------------------------------------------------------------------
# 1. Fully compliant quotation
# ---------------------------------------------------------------------------

class TestFullyCompliant:
    def test_status_is_compliant(self):
        svc = ComplianceService()
        eq  = make_eq()
        r   = svc.evaluate(eq, [make_item()])
        assert r.status == ComplianceStatus.COMPLIANT

    def test_no_issues(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(), [make_item()])
        assert r.failed_checks == 0
        assert r.warning_count == 0
        assert r.issues == []

    def test_passed_checks_positive(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(), [make_item()])
        assert r.passed_checks > 0


# ---------------------------------------------------------------------------
# 2. Document completeness failures
# ---------------------------------------------------------------------------

class TestDocumentCompleteness:

    def test_missing_vendor_name_is_error(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(vendor_name=None), [])
        names = [i.check_name for i in r.issues if i.severity == Severity.ERROR]
        assert "vendor_name_present" in names
        assert r.status == ComplianceStatus.NON_COMPLIANT

    def test_missing_gst_number_is_warning(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(vendor_gst_number=None), [])
        warnings = [i.check_name for i in r.issues if i.severity == Severity.WARNING]
        assert "gst_number_present" in warnings
        # No errors from this alone → partially compliant
        assert r.status in (ComplianceStatus.PARTIALLY_COMPLIANT, ComplianceStatus.COMPLIANT)

    def test_missing_quotation_number_is_error(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(quotation_number=None), [])
        names = [i.check_name for i in r.issues if i.severity == Severity.ERROR]
        assert "quotation_number_present" in names

    def test_missing_currency_is_error(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(currency=None), [])
        names = [i.check_name for i in r.issues if i.severity == Severity.ERROR]
        assert "currency_present" in names

    def test_missing_grand_total_is_error(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(grand_total=None), [])
        names = [i.check_name for i in r.issues if i.severity == Severity.ERROR]
        assert "grand_total_present" in names


# ---------------------------------------------------------------------------
# 3. Commercial terms
# ---------------------------------------------------------------------------

class TestCommercialTerms:

    def test_missing_payment_terms_is_warning(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(payment_terms=None), [])
        names = [i.check_name for i in r.issues if i.severity == Severity.WARNING]
        assert "payment_terms_present" in names
        assert r.status == ComplianceStatus.PARTIALLY_COMPLIANT

    def test_missing_delivery_time_is_warning(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(delivery_time=None), [])
        names = [i.check_name for i in r.issues if i.severity == Severity.WARNING]
        assert "delivery_time_present" in names

    def test_missing_warranty_is_warning(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(warranty=None), [])
        names = [i.check_name for i in r.issues if i.severity == Severity.WARNING]
        assert "warranty_present" in names


# ---------------------------------------------------------------------------
# 4. Pricing validation
# ---------------------------------------------------------------------------

class TestPricingValidation:

    def test_negative_grand_total_is_error(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(grand_total=Decimal("-1")), [])
        names = [i.check_name for i in r.issues if i.severity == Severity.ERROR]
        assert "grand_total_non_negative" in names
        assert r.status == ComplianceStatus.NON_COMPLIANT

    def test_negative_subtotal_is_error(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(subtotal=Decimal("-500")), [])
        names = [i.check_name for i in r.issues]
        assert "subtotal_non_negative" in names

    def test_negative_discount_is_error(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(discount=Decimal("-100")), [])
        names = [i.check_name for i in r.issues]
        assert "discount_non_negative" in names

    def test_negative_tax_is_error(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(tax=Decimal("-200")), [])
        names = [i.check_name for i in r.issues]
        assert "tax_non_negative" in names
        assert r.status == ComplianceStatus.NON_COMPLIANT

    def test_negative_shipping_cost_is_error(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(shipping_cost=Decimal("-50")), [])
        names = [i.check_name for i in r.issues]
        assert "shipping_cost_non_negative" in names
        assert r.status == ComplianceStatus.NON_COMPLIANT

    def test_zero_values_are_valid(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(discount=Decimal("0"), tax=Decimal("0"), shipping_cost=Decimal("0")), [])
        pricing_errors = [i for i in r.issues if "non_negative" in i.check_name and i.severity == Severity.ERROR]
        assert pricing_errors == []


# ---------------------------------------------------------------------------
# 5. Date validation
# ---------------------------------------------------------------------------

class TestDateValidation:

    def test_expired_quotation_is_error(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(valid_until=PAST_DATE), [])
        names = [i.check_name for i in r.issues if i.severity == Severity.ERROR]
        assert "valid_until_not_expired" in names
        assert r.status == ComplianceStatus.NON_COMPLIANT

    def test_future_quotation_date_is_warning(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(quotation_date=FUTURE_DATE), [])
        names = [i.check_name for i in r.issues if i.severity == Severity.WARNING]
        assert "quotation_date_not_future" in names

    def test_valid_future_valid_until_passes(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(valid_until=FAR_FUTURE), [])
        names = [i.check_name for i in r.issues]
        assert "valid_until_not_expired" not in names

    def test_unparseable_date_silently_skipped(self):
        """Unparseable dates should not cause a check failure."""
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(valid_until="expires soon", quotation_date="July 2026"), [])
        # No crash; no error for unparseable
        date_errors = [i for i in r.issues if "valid_until" in i.check_name]
        assert date_errors == []


# ---------------------------------------------------------------------------
# 6. Items validation
# ---------------------------------------------------------------------------

class TestItemsValidation:

    def test_missing_item_name_is_warning(self):
        svc  = ComplianceService()
        item = make_item(item_name=None)
        r    = svc.evaluate(make_eq(), [item])
        names = [i.check_name for i in r.issues if i.severity == Severity.WARNING]
        assert "items_item_name_present" in names

    def test_zero_quantity_is_error(self):
        svc  = ComplianceService()
        item = make_item(quantity=Decimal("0"))
        r    = svc.evaluate(make_eq(), [item])
        names = [i.check_name for i in r.issues if i.severity == Severity.ERROR]
        assert "items_quantity_positive" in names

    def test_negative_quantity_is_error(self):
        svc  = ComplianceService()
        item = make_item(quantity=Decimal("-1"))
        r    = svc.evaluate(make_eq(), [item])
        assert "items_quantity_positive" in [i.check_name for i in r.issues]

    def test_negative_unit_price_is_error(self):
        svc  = ComplianceService()
        item = make_item(unit_price=Decimal("-500"))
        r    = svc.evaluate(make_eq(), [item])
        names = [i.check_name for i in r.issues]
        assert "items_unit_price_non_negative" in names

    def test_negative_total_price_is_error(self):
        svc  = ComplianceService()
        item = make_item(total_price=Decimal("-1000"))
        r    = svc.evaluate(make_eq(), [item])
        names = [i.check_name for i in r.issues]
        assert "items_total_price_non_negative" in names

    def test_zero_prices_are_valid(self):
        svc  = ComplianceService()
        item = make_item(unit_price=Decimal("0"), total_price=Decimal("0"), quantity=Decimal("1"))
        r    = svc.evaluate(make_eq(), [item])
        price_errors = [i for i in r.issues if "price_non_negative" in i.check_name]
        assert price_errors == []

    def test_no_items_skips_item_checks(self):
        svc = ComplianceService()
        r   = svc.evaluate(make_eq(), items=[])
        item_issues = [i for i in r.issues if i.check_name.startswith("items_")]
        assert item_issues == []


# ---------------------------------------------------------------------------
# 7. Multiple simultaneous failures
# ---------------------------------------------------------------------------

class TestMultipleFailures:

    def test_multiple_errors_all_captured(self):
        svc = ComplianceService()
        eq  = make_eq(
            vendor_name=None,
            currency=None,
            grand_total=Decimal("-500"),
            valid_until=PAST_DATE,
        )
        r = svc.evaluate(eq, [])
        check_names = [i.check_name for i in r.issues]
        assert "vendor_name_present"      in check_names
        assert "currency_present"         in check_names
        assert "grand_total_non_negative" in check_names
        assert "valid_until_not_expired"  in check_names
        assert r.failed_checks >= 4
        assert r.status == ComplianceStatus.NON_COMPLIANT

    def test_mixed_errors_and_warnings(self):
        """Error takes precedence: status is NON_COMPLIANT even with warnings."""
        svc = ComplianceService()
        eq  = make_eq(grand_total=Decimal("-1"), payment_terms=None, warranty=None)
        r   = svc.evaluate(eq, [])
        assert r.failed_checks >= 1
        assert r.warning_count >= 2
        assert r.status == ComplianceStatus.NON_COMPLIANT


# ---------------------------------------------------------------------------
# 8. Empty project (agent level)
# ---------------------------------------------------------------------------

class TestEmptyProject:

    def test_empty_project_returns_success(self):
        from app.agents.compliance_agent import ComplianceAgent
        db    = MagicMock()
        agent = ComplianceAgent(db=db, generate_summary=False)
        with patch.object(agent._repo, "get_by_project_id", return_value=[]):
            result = agent.evaluate(uuid.uuid4())
        assert result.success is True
        assert result.data.total_quotations == 0
        assert result.data.compliant_count == 0

    def test_empty_project_has_no_errors_field(self):
        from app.agents.compliance_agent import ComplianceAgent
        db    = MagicMock()
        agent = ComplianceAgent(db=db, generate_summary=False)
        with patch.object(agent._repo, "get_by_project_id", return_value=[]):
            result = agent.evaluate(uuid.uuid4())
        assert result.errors == []


# ---------------------------------------------------------------------------
# 9. Repository failure
# ---------------------------------------------------------------------------

class TestRepositoryFailure:

    def test_db_error_returns_structured_failure(self):
        from app.agents.compliance_agent import ComplianceAgent
        db    = MagicMock()
        agent = ComplianceAgent(db=db, generate_summary=False)
        with patch.object(agent._repo, "get_by_project_id", side_effect=RuntimeError("DB down")):
            result = agent.evaluate(uuid.uuid4())
        assert result.success is False
        assert "Database error" in result.errors[0]
        assert result.data is None


# ---------------------------------------------------------------------------
# 10. Optional LLM summary
# ---------------------------------------------------------------------------

class TestLLMSummary:

    def _make_agent_with_vendors(self, llm_return: str | None):
        from app.agents.compliance_agent import ComplianceAgent
        from app.services.llm_service import LLMService

        db = MagicMock()
        mock_llm = MagicMock(spec=LLMService)
        if llm_return is not None:
            mock_llm.complete_json.return_value = llm_return
        else:
            mock_llm.complete_json.side_effect = RuntimeError("Mistral timeout")

        agent = ComplianceAgent(db=db, llm_service=mock_llm, generate_summary=True)

        eq = make_eq()
        eq.items = []
        with patch.object(agent._repo, "get_by_project_id", return_value=[eq]):
            result = agent.evaluate(uuid.uuid4())
        return result

    def test_llm_summary_success_plain_text(self):
        result = self._make_agent_with_vendors("All vendors passed compliance checks.")
        assert result.success is True
        assert result.data.summary is not None

    def test_llm_summary_success_json_wrapped(self):
        import json
        wrapped = json.dumps({"summary": "Two vendors assessed. One is non-compliant."})
        result  = self._make_agent_with_vendors(wrapped)
        assert result.success is True
        assert "Two vendors" in result.data.summary

    def test_llm_summary_failure_is_non_fatal(self):
        """LLM timeout must not fail the compliance evaluation."""
        result = self._make_agent_with_vendors(llm_return=None)
        assert result.success is True
        assert result.data.summary is None   # skipped, not crashed

    def test_no_llm_no_summary(self):
        from app.agents.compliance_agent import ComplianceAgent
        db    = MagicMock()
        agent = ComplianceAgent(db=db, llm_service=None, generate_summary=False)
        eq    = make_eq()
        eq.items = []
        with patch.object(agent._repo, "get_by_project_id", return_value=[eq]):
            result = agent.evaluate(uuid.uuid4())
        assert result.success is True
        assert result.data.summary is None


# ---------------------------------------------------------------------------
# 11. Aggregate statistics (agent level)
# ---------------------------------------------------------------------------

class TestAggregateStatistics:

    def test_counts_are_correct(self):
        from app.agents.compliance_agent import ComplianceAgent
        db    = MagicMock()
        agent = ComplianceAgent(db=db, generate_summary=False)

        compliant_eq    = make_eq(vendor_name="Alpha")
        partial_eq      = make_eq(vendor_name="Beta",  warranty=None)  # warning only
        noncompliant_eq = make_eq(vendor_name="Gamma", grand_total=Decimal("-1"))

        for eq in [compliant_eq, partial_eq, noncompliant_eq]:
            eq.items = []

        with patch.object(agent._repo, "get_by_project_id",
                          return_value=[compliant_eq, partial_eq, noncompliant_eq]):
            result = agent.evaluate(uuid.uuid4())

        assert result.data.total_quotations          == 3
        assert result.data.compliant_count           == 1
        assert result.data.partially_compliant_count == 1
        assert result.data.non_compliant_count       == 1
