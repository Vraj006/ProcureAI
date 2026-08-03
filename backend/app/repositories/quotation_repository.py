"""
Quotation repository.

All database access for Quotation records — SQLAlchemy 2.x style.
"""

import math
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.quotation import Quotation


class QuotationRepository:
    """Data-access object for the Quotation model."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, quotation_id: uuid.UUID) -> Quotation | None:
        """Return an active quotation by primary key, or None."""
        stmt = select(Quotation).where(
            Quotation.id == quotation_id,
            Quotation.is_deleted.is_(False),
        )
        return self._db.scalars(stmt).first()

    def get_by_id_in_project(
        self, quotation_id: uuid.UUID, project_id: uuid.UUID
    ) -> Quotation | None:
        """Return an active quotation belonging to a specific project."""
        stmt = select(Quotation).where(
            Quotation.id == quotation_id,
            Quotation.project_id == project_id,
            Quotation.is_deleted.is_(False),
        )
        return self._db.scalars(stmt).first()

    def get_by_number_in_project(
        self, quotation_number: str, project_id: uuid.UUID
    ) -> Quotation | None:
        """
        Check for a duplicate quotation number within the same project.

        Returns the existing quotation if found, None otherwise.
        """
        stmt = select(Quotation).where(
            Quotation.quotation_number == quotation_number,
            Quotation.project_id == project_id,
            Quotation.is_deleted.is_(False),
        )
        return self._db.scalars(stmt).first()

    def list_by_project(
        self,
        project_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Quotation], int]:
        """Return a paginated list of quotations for a project."""
        page_size = max(1, min(page_size, 100))
        offset = (max(1, page) - 1) * page_size

        filters = [
            Quotation.project_id == project_id,
            Quotation.is_deleted.is_(False),
        ]

        total: int = self._db.scalar(
            select(func.count()).select_from(Quotation).where(*filters)
        ) or 0

        items = list(
            self._db.scalars(
                select(Quotation)
                .where(*filters)
                .order_by(Quotation.created_at.desc())
                .offset(offset)
                .limit(page_size)
            ).all()
        )
        return items, total

    def create(self, quotation: Quotation) -> Quotation:
        self._db.add(quotation)
        self._db.flush()
        self._db.refresh(quotation)
        return quotation

    def update(self, quotation: Quotation) -> Quotation:
        self._db.flush()
        self._db.refresh(quotation)
        return quotation

    def soft_delete(self, quotation: Quotation) -> None:
        quotation.is_deleted = True
        self._db.flush()
