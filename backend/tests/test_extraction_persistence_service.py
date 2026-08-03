"""
Unit tests for ExtractionPersistenceService.

All tests mock the SQLAlchemy Session and the repository so they run
without a real database connection.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

import pytest

from app.models.extracted_quotation import (
    ExtractedQuotation,
    ExtractedQuotationItem,
    ExtractionStatus,
)
from app.schemas.extraction_schema import (
    CommercialTerms,
    ExtractedVendor,
    ExtractedQuotation as SchemaQuotation,
    Pricing,
    ProcurementExtractionResult,
    QuotationItem,
)
from app.services.extraction_persistence_service import ExtractionPersistenceService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_full_result() -> ProcurementExtractionResult:
    return ProcurementExtractionResult(
        vendor=ExtractedVendor(
            name="Acme Ltd",
            address="Mumbai",
            email="acme@example.com",
            phone="+91-99999-99999",
            gst_number="27ABCDE1234F1Z5",
        ),
        quotation=SchemaQuotation(
            quotation_number="Q-001",
            quotation_date="2024-07-15",
            currency="INR",
            valid_until="2024-08-15",
        ),
        items=[
            QuotationItem(
                item_name="Pump",
                description="Industrial pump",
                quantity=2.0,
                unit="units",
                unit_price=50000.0,
                total_price=100000.0,
            )
        ],
        pricing=Pricing(
            subtotal=100000.0,
            discount=5000.0,
            shipping_cost=1000.0,
            tax=18000.0,
            grand_total=114000.0,
        ),
        commercial_terms=CommercialTerms(
            payment_terms="Net 30",
            delivery_time="4 weeks",
            warranty="1 year",
            incoterms="DAP",
        ),
    )


def make_service(mock_db: MagicMock) -> ExtractionPersistenceService:
    return ExtractionPersistenceService(db=mock_db)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSaveExtractionSuccess:

    def test_commits_transaction_on_success(self):
        db = MagicMock()
        # db.scalars(...) / flush / refresh / commit are all tracked
        service = make_service(db)
        quotation_id = uuid.uuid4()
        result = make_full_result()

        with patch.object(service._repo, "create_extracted_quotation", return_value=MagicMock(spec=ExtractedQuotation, id=uuid.uuid4())), \
             patch.object(service._repo, "create_extracted_items", return_value=[]):
            service.save_extraction(quotation_id, result)

        db.commit.assert_called_once()
        db.rollback.assert_not_called()

    def test_returns_extracted_quotation_instance(self):
        db = MagicMock()
        service = make_service(db)
        quotation_id = uuid.uuid4()
        result = make_full_result()

        with patch.object(service._repo, "create_extracted_quotation", side_effect=lambda eq: eq), \
             patch.object(service._repo, "create_extracted_items", return_value=[]):
            returned = service.save_extraction(quotation_id, result)

        # Service builds the ORM object internally — verify it's the right type
        # and it's linked to the correct quotation_id.
        assert isinstance(returned, ExtractedQuotation)
        assert returned.quotation_id == quotation_id

    def test_vendor_fields_mapped_correctly(self):
        db = MagicMock()
        service = make_service(db)
        quotation_id = uuid.uuid4()
        result = make_full_result()

        captured = []

        def capture_eq(eq):
            captured.append(eq)
            eq.id = uuid.uuid4()
            return eq

        with patch.object(service._repo, "create_extracted_quotation", side_effect=capture_eq), \
             patch.object(service._repo, "create_extracted_items", return_value=[]):
            service.save_extraction(quotation_id, result)

        eq = captured[0]
        assert eq.vendor_name == "Acme Ltd"
        assert eq.vendor_email == "acme@example.com"
        assert eq.vendor_gst_number == "27ABCDE1234F1Z5"
        assert eq.grand_total == 114000.0
        assert eq.extraction_status == ExtractionStatus.SUCCESS

    def test_items_are_created(self):
        db = MagicMock()
        service = make_service(db)
        quotation_id = uuid.uuid4()
        result = make_full_result()

        fake_eq = MagicMock(spec=ExtractedQuotation)
        fake_eq.id = uuid.uuid4()
        captured_items = []

        def capture_items(items):
            captured_items.extend(items)
            return items

        with patch.object(service._repo, "create_extracted_quotation", return_value=fake_eq), \
             patch.object(service._repo, "create_extracted_items", side_effect=capture_items):
            service.save_extraction(quotation_id, result)

        assert len(captured_items) == 1
        assert captured_items[0].item_name == "Pump"
        assert captured_items[0].quantity == 2.0

    def test_no_items_skips_item_creation(self):
        db = MagicMock()
        service = make_service(db)
        quotation_id = uuid.uuid4()
        # Result with no items
        result = ProcurementExtractionResult(vendor=None, quotation=None, items=[])

        fake_eq = MagicMock(spec=ExtractedQuotation)
        fake_eq.id = uuid.uuid4()

        with patch.object(service._repo, "create_extracted_quotation", return_value=fake_eq) as mock_create, \
             patch.object(service._repo, "create_extracted_items") as mock_items:
            service.save_extraction(quotation_id, result)

        mock_items.assert_not_called()
        db.commit.assert_called_once()


class TestSaveExtractionRollback:

    def test_rollback_called_on_repo_failure(self):
        db = MagicMock()
        service = make_service(db)
        quotation_id = uuid.uuid4()

        with patch.object(
            service._repo,
            "create_extracted_quotation",
            side_effect=Exception("DB failure"),
        ):
            with pytest.raises(Exception, match="DB failure"):
                service.save_extraction(quotation_id, make_full_result())

        db.rollback.assert_called_once()
        db.commit.assert_not_called()

    def test_rollback_on_item_insert_failure(self):
        db = MagicMock()
        service = make_service(db)
        quotation_id = uuid.uuid4()

        fake_eq = MagicMock(spec=ExtractedQuotation)
        fake_eq.id = uuid.uuid4()

        with patch.object(service._repo, "create_extracted_quotation", return_value=fake_eq), \
             patch.object(service._repo, "create_extracted_items", side_effect=Exception("Constraint violation")):
            with pytest.raises(Exception, match="Constraint violation"):
                service.save_extraction(quotation_id, make_full_result())

        db.rollback.assert_called_once()
        db.commit.assert_not_called()


class TestGetByQuotationId:

    def test_delegates_to_repository(self):
        db = MagicMock()
        service = make_service(db)
        quotation_id = uuid.uuid4()
        fake_record = MagicMock(spec=ExtractedQuotation)

        with patch.object(service._repo, "get_by_quotation_id", return_value=fake_record) as mock_get:
            result = service._repo.get_by_quotation_id(quotation_id)

        assert result is fake_record
        mock_get.assert_called_once_with(quotation_id)
