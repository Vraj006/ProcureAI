"""
Extraction Persistence Service.

Bridges the AI extraction layer and the database.

Responsibilities:
- Accept a validated ProcurementExtractionResult + the source quotation_id.
- Map the Pydantic object onto SQLAlchemy models.
- Persist header + all line items in a single atomic transaction.
- Roll back the transaction if anything fails.
- Return the persisted ExtractedQuotation ORM instance.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.extracted_quotation import (
    ExtractedQuotation,
    ExtractedQuotationItem,
    ExtractionStatus,
)
from app.repositories.extracted_quotation_repository import (
    ExtractedQuotationRepository,
)
from app.schemas.extraction_schema import ProcurementExtractionResult

logger = get_logger(__name__)

# The Mistral model used for extraction (matches llm_service default).
# Stored alongside each record so analysts can filter by model version.
_DEFAULT_EXTRACTION_MODEL = "mistral-small-latest"


class ExtractionPersistenceService:
    """
    Saves a validated ProcurementExtractionResult to PostgreSQL.

    Usage::

        service = ExtractionPersistenceService(db)
        record = service.save_extraction(quotation_id, validated_result)
    """

    def __init__(
        self,
        db: Session,
        extraction_model: str = _DEFAULT_EXTRACTION_MODEL,
    ) -> None:
        self._db = db
        self._repo = ExtractedQuotationRepository(db)
        self._extraction_model = extraction_model

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def save_extraction(
        self,
        quotation_id: uuid.UUID,
        validated_result: ProcurementExtractionResult,
    ) -> ExtractedQuotation:
        """
        Persist a validated extraction result in a single transaction.

        If any insert fails the entire transaction is rolled back and the
        exception is re-raised so the caller can handle it appropriately.

        Args:
            quotation_id:     UUID of the source Quotation record.
            validated_result: Pydantic model returned by ExtractionAgent.

        Returns:
            The newly created ExtractedQuotation ORM instance (with id).
        """
        logger.info(
            "Persisting extraction for quotation_id=%s", quotation_id
        )

        try:
            # ── 1. Build and persist the header row ─────────────────────
            extracted = self._build_extracted_quotation(quotation_id, validated_result)
            self._repo.create_extracted_quotation(extracted)

            # ── 2. Build and persist line items ──────────────────────────
            if validated_result.items:
                items = [
                    self._build_item(extracted.id, item)
                    for item in validated_result.items
                ]
                self._repo.create_extracted_items(items)
                extracted.items = items  # attach to the returned object

            # ── 3. Commit the transaction ─────────────────────────────────
            self._db.commit()
            self._db.refresh(extracted)

            logger.info(
                "Extraction persisted — extracted_quotation.id=%s  items=%d",
                extracted.id,
                len(validated_result.items),
            )
            return extracted

        except Exception as exc:
            logger.error(
                "Failed to persist extraction for quotation_id=%s: %s",
                quotation_id,
                exc,
            )
            self._db.rollback()
            raise

    # ------------------------------------------------------------------
    # Private mapping helpers
    # ------------------------------------------------------------------

    def _build_extracted_quotation(
        self,
        quotation_id: uuid.UUID,
        result: ProcurementExtractionResult,
    ) -> ExtractedQuotation:
        """Map ProcurementExtractionResult → ExtractedQuotation ORM instance."""
        vendor = result.vendor
        quotation = result.quotation
        pricing = result.pricing
        terms = result.commercial_terms

        return ExtractedQuotation(
            quotation_id=quotation_id,
            # --- Vendor ---
            vendor_name=vendor.name if vendor else None,
            vendor_address=vendor.address if vendor else None,
            vendor_email=vendor.email if vendor else None,
            vendor_phone=vendor.phone if vendor else None,
            vendor_gst_number=vendor.gst_number if vendor else None,
            # --- Quotation header ---
            quotation_number=quotation.quotation_number if quotation else None,
            quotation_date=quotation.quotation_date if quotation else None,
            currency=quotation.currency if quotation else None,
            valid_until=quotation.valid_until if quotation else None,
            # --- Pricing ---
            subtotal=pricing.subtotal if pricing else None,
            discount=pricing.discount if pricing else None,
            shipping_cost=pricing.shipping_cost if pricing else None,
            tax=pricing.tax if pricing else None,
            grand_total=pricing.grand_total if pricing else None,
            # --- Commercial terms ---
            payment_terms=terms.payment_terms if terms else None,
            delivery_time=terms.delivery_time if terms else None,
            warranty=terms.warranty if terms else None,
            incoterms=terms.incoterms if terms else None,
            # --- Extraction metadata ---
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_model=self._extraction_model,
            extracted_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _build_item(
        extracted_quotation_id: uuid.UUID,
        item,   # QuotationItem from extraction_schema
    ) -> ExtractedQuotationItem:
        """Map a QuotationItem → ExtractedQuotationItem ORM instance."""
        return ExtractedQuotationItem(
            extracted_quotation_id=extracted_quotation_id,
            item_name=item.item_name,
            description=item.description,
            quantity=item.quantity,
            unit=item.unit,
            unit_price=item.unit_price,
            total_price=item.total_price,
        )
