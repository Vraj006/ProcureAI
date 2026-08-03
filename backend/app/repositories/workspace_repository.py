"""
Workspace repository.

Encapsulates all database access for Workspace records.
All queries filter out soft-deleted records by default.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workspace import Workspace


class WorkspaceRepository:
    """Data-access object for the Workspace model."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, workspace_id: uuid.UUID) -> Workspace | None:
        """Return an active workspace by primary key, or None."""
        stmt = select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.is_deleted.is_(False),
        )
        return self._db.scalars(stmt).first()

    def list_by_owner(self, owner_id: uuid.UUID) -> list[Workspace]:
        """Return all active workspaces owned by a given user."""
        stmt = (
            select(Workspace)
            .where(
                Workspace.owner_id == owner_id,
                Workspace.is_deleted.is_(False),
            )
            .order_by(Workspace.created_at.desc())
        )
        return list(self._db.scalars(stmt).all())

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, workspace: Workspace) -> Workspace:
        """Persist a new Workspace and return it after flush."""
        self._db.add(workspace)
        self._db.flush()
        self._db.refresh(workspace)
        return workspace

    def update(self, workspace: Workspace) -> Workspace:
        """Flush pending changes for a tracked Workspace and return it."""
        self._db.flush()
        self._db.refresh(workspace)
        return workspace

    def soft_delete(self, workspace: Workspace) -> None:
        """Mark a workspace as deleted."""
        workspace.is_deleted = True
        self._db.flush()
