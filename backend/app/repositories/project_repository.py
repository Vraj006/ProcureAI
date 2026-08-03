"""
Procurement Project repository.

Encapsulates all DB access for ProcurementProject records,
including full-text search and cursor-based pagination.
"""

import math
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.project import ProcurementProject


class ProjectRepository:
    """Data-access object for the ProcurementProject model."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, project_id: uuid.UUID) -> ProcurementProject | None:
        """Return an active project by primary key, or None."""
        stmt = select(ProcurementProject).where(
            ProcurementProject.id == project_id,
            ProcurementProject.is_deleted.is_(False),
        )
        return self._db.scalars(stmt).first()

    def list_by_workspace(
        self,
        workspace_id: uuid.UUID,
        *,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ProcurementProject], int]:
        """
        Return a paginated list of projects within a workspace.

        Args:
            workspace_id: Filter to this workspace.
            search: Optional substring to match against name or description.
            page: 1-indexed page number.
            page_size: Maximum items per page (clamped to 1–100).

        Returns:
            Tuple of (items, total_count).
        """
        page_size = max(1, min(page_size, 100))
        offset = (max(1, page) - 1) * page_size

        base_filter = [
            ProcurementProject.workspace_id == workspace_id,
            ProcurementProject.is_deleted.is_(False),
        ]

        if search:
            pattern = f"%{search}%"
            base_filter.append(
                or_(
                    ProcurementProject.name.ilike(pattern),
                    ProcurementProject.description.ilike(pattern),
                )
            )

        # Total count
        count_stmt = select(func.count()).select_from(ProcurementProject).where(*base_filter)
        total: int = self._db.scalar(count_stmt) or 0

        # Paginated items
        items_stmt = (
            select(ProcurementProject)
            .where(*base_filter)
            .order_by(ProcurementProject.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(self._db.scalars(items_stmt).all())

        return items, total

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, project: ProcurementProject) -> ProcurementProject:
        """Persist a new project and return it after flush."""
        self._db.add(project)
        self._db.flush()
        self._db.refresh(project)
        return project

    def update(self, project: ProcurementProject) -> ProcurementProject:
        """Flush pending changes for a tracked project and return it."""
        self._db.flush()
        self._db.refresh(project)
        return project

    def soft_delete(self, project: ProcurementProject) -> None:
        """Mark a project as deleted."""
        project.is_deleted = True
        self._db.flush()
