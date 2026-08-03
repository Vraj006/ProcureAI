"""
Workspace service.

Business logic for workspace lifecycle management.
Enforces ownership — only the owner may modify or delete a workspace.
"""

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.models.workspace import Workspace
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate

logger = get_logger(__name__)


class WorkspaceService:
    """Manages workspace creation, retrieval, update, and deletion."""

    def __init__(self, db: Session) -> None:
        self._repo = WorkspaceRepository(db)
        self._db = db

    def get_workspace(self, workspace_id: uuid.UUID, requesting_user_id: uuid.UUID) -> Workspace:
        """
        Retrieve a workspace, enforcing ownership.

        Raises:
            NotFoundError: If the workspace doesn't exist.
            ForbiddenError: If the requester is not the owner.
        """
        workspace = self._repo.get_by_id(workspace_id)
        if not workspace:
            raise NotFoundError(message=f"Workspace {workspace_id} not found")
        if workspace.owner_id != requesting_user_id:
            raise ForbiddenError()
        return workspace

    def list_workspaces(self, owner_id: uuid.UUID) -> list[Workspace]:
        """Return all active workspaces owned by the given user."""
        return self._repo.list_by_owner(owner_id)

    def create_workspace(self, data: WorkspaceCreate, owner_id: uuid.UUID) -> Workspace:
        """Create and persist a new workspace."""
        workspace = Workspace(
            name=data.name,
            description=data.description,
            owner_id=owner_id,
        )
        self._repo.create(workspace)
        self._db.commit()
        self._db.refresh(workspace)
        logger.info("Workspace '%s' created by user %s", workspace.name, owner_id)
        return workspace

    def update_workspace(
        self,
        workspace_id: uuid.UUID,
        data: WorkspaceUpdate,
        requesting_user_id: uuid.UUID,
    ) -> Workspace:
        """
        Apply a partial update to a workspace.

        Raises:
            NotFoundError / ForbiddenError: From get_workspace.
        """
        workspace = self.get_workspace(workspace_id, requesting_user_id)

        if data.name is not None:
            workspace.name = data.name
        if data.description is not None:
            workspace.description = data.description

        self._repo.update(workspace)
        self._db.commit()
        self._db.refresh(workspace)
        logger.info("Workspace %s updated", workspace_id)
        return workspace

    def delete_workspace(self, workspace_id: uuid.UUID, requesting_user_id: uuid.UUID) -> None:
        """
        Soft-delete a workspace.

        Raises:
            NotFoundError / ForbiddenError: From get_workspace.
        """
        workspace = self.get_workspace(workspace_id, requesting_user_id)
        self._repo.soft_delete(workspace)
        self._db.commit()
        logger.info("Workspace %s soft-deleted by user %s", workspace_id, requesting_user_id)
