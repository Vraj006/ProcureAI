"""
Repository for ExtractedQuotation and ExtractedQuotationItem.

All raw DB access for extraction results — SQLAlchemy 2.x style.
No business logic here; services own the transaction boundary.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.extracted_quotation import ExtractedQuotation, ExtractedQuotationItem


class ExtractedQuotationRepository:
    """Data-access object for extraction result records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Write operations (called inside an open transaction from the service)
    # ------------------------------------------------------------------

    def create_extracted_quotation(
        self, extracted_quotation: ExtractedQuotation
    ) -> ExtractedQuotation:
        """
        Persist a new ExtractedQuotation row.

        Uses ``flush()`` (not ``commit()``) so the service layer controls
        the transaction boundary.
        """
        self._db.add(extracted_quotation)
        self._db.flush()
        self._db.refresh(extracted_quotation)
        return extracted_quotation

    def create_extracted_items(
        self, items: list[ExtractedQuotationItem]
    ) -> list[ExtractedQuotationItem]:
        """
        Bulk-insert a list of ExtractedQuotationItem rows in the open transaction.

        Returns the flushed (id-assigned) items.
        """
        if not items:
            return []
        self._db.add_all(items)
        self._db.flush()
        for item in items:
            self._db.refresh(item)
        return items

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_by_quotation_id(
        self, quotation_id: uuid.UUID
    ) -> ExtractedQuotation | None:
        """
        Return the ExtractedQuotation for a given source Quotation ID.

        Returns None if no extraction has been persisted yet.
        """
        stmt = select(ExtractedQuotation).where(
            ExtractedQuotation.quotation_id == quotation_id
        )
        return self._db.scalars(stmt).first()

    def get_by_project_id(
        self, project_id: uuid.UUID
    ) -> list[ExtractedQuotation]:
        """
        Return all SUCCESSFUL extracted quotations for a given project.

        Joins ExtractedQuotation → Quotation to filter by project scope.
        Only includes rows with extraction_status=SUCCESS and whose source
        Quotation is not soft-deleted.
        """
        from app.models.extracted_quotation import ExtractionStatus
        from app.models.quotation import Quotation  # local import avoids circular dep

        stmt = (
            select(ExtractedQuotation)
            .join(Quotation, ExtractedQuotation.quotation_id == Quotation.id)
            .where(
                Quotation.project_id == project_id,
                Quotation.is_deleted.is_(False),
                ExtractedQuotation.extraction_status == ExtractionStatus.SUCCESS,
            )
        )
        return list(self._db.scalars(stmt).all())
