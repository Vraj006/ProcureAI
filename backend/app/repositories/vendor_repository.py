"""
Vendor repository.

All database access for Vendor records — SQLAlchemy 2.x style.
"""

import math
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.vendor import Vendor


class VendorRepository:
    """Data-access object for the Vendor model."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, vendor_id: uuid.UUID) -> Vendor | None:
        """Return an active vendor by primary key, or None."""
        stmt = select(Vendor).where(
            Vendor.id == vendor_id,
            Vendor.is_deleted.is_(False),
        )
        return self._db.scalars(stmt).first()

    def get_by_id_in_workspace(
        self, vendor_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> Vendor | None:
        """Return an active vendor by ID that belongs to the given workspace."""
        stmt = select(Vendor).where(
            Vendor.id == vendor_id,
            Vendor.workspace_id == workspace_id,
            Vendor.is_deleted.is_(False),
        )
        return self._db.scalars(stmt).first()

    def list_by_workspace(
        self,
        workspace_id: uuid.UUID,
        *,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Vendor], int]:
        """
        Return a paginated list of vendors in a workspace.

        Search matches company_name (case-insensitive).
        """
        page_size = max(1, min(page_size, 100))
        offset = (max(1, page) - 1) * page_size

        filters = [
            Vendor.workspace_id == workspace_id,
            Vendor.is_deleted.is_(False),
        ]
        if search:
            filters.append(Vendor.company_name.ilike(f"%{search}%"))

        total: int = self._db.scalar(
            select(func.count()).select_from(Vendor).where(*filters)
        ) or 0

        items = list(
            self._db.scalars(
                select(Vendor)
                .where(*filters)
                .order_by(Vendor.company_name.asc())
                .offset(offset)
                .limit(page_size)
            ).all()
        )
        return items, total

    def create(self, vendor: Vendor) -> Vendor:
        self._db.add(vendor)
        self._db.flush()
        self._db.refresh(vendor)
        return vendor

    def update(self, vendor: Vendor) -> Vendor:
        self._db.flush()
        self._db.refresh(vendor)
        return vendor

    def soft_delete(self, vendor: Vendor) -> None:
        vendor.is_deleted = True
        self._db.flush()
