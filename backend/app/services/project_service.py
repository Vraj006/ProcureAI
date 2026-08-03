"""
Procurement Project service.

Business logic for project lifecycle management.
Verifies workspace membership before granting access.
"""

import math
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.models.project import ProcurementProject
from app.repositories.project_repository import ProjectRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.project import PaginatedProjectResponse, ProjectCreate, ProjectResponse, ProjectUpdate

logger = get_logger(__name__)


class ProjectService:
    """Manages procurement project CRUD with workspace membership checks."""

    def __init__(self, db: Session) -> None:
        self._repo = ProjectRepository(db)
        self._ws_repo = WorkspaceRepository(db)
        self._db = db

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _assert_workspace_access(
        self, workspace_id: uuid.UUID, requesting_user_id: uuid.UUID
    ) -> None:
        """
        Verify that the workspace exists and belongs to the requesting user.

        Raises:
            NotFoundError: If workspace is not found.
            ForbiddenError: If user is not the owner.
        """
        workspace = self._ws_repo.get_by_id(workspace_id)
        if not workspace:
            raise NotFoundError(message=f"Workspace {workspace_id} not found")
        if workspace.owner_id != requesting_user_id:
            raise ForbiddenError()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_project(
        self, workspace_id: uuid.UUID, project_id: uuid.UUID, requesting_user_id: uuid.UUID
    ) -> ProcurementProject:
        """
        Retrieve a project by ID, confirming workspace access first.

        Raises:
            NotFoundError / ForbiddenError.
        """
        self._assert_workspace_access(workspace_id, requesting_user_id)
        project = self._repo.get_by_id(project_id)
        if not project or project.workspace_id != workspace_id:
            raise NotFoundError(message=f"Project {project_id} not found in workspace {workspace_id}")
        return project

    def list_projects(
        self,
        workspace_id: uuid.UUID,
        requesting_user_id: uuid.UUID,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedProjectResponse:
        """
        Return a paginated list of projects in a workspace.

        Raises:
            NotFoundError / ForbiddenError.
        """
        self._assert_workspace_access(workspace_id, requesting_user_id)
        items, total = self._repo.list_by_workspace(
            workspace_id, search=search, page=page, page_size=page_size
        )
        pages = math.ceil(total / page_size) if page_size else 1

        return PaginatedProjectResponse(
            items=[ProjectResponse.model_validate(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def create_project(
        self, workspace_id: uuid.UUID, data: ProjectCreate, requesting_user_id: uuid.UUID
    ) -> ProcurementProject:
        """Create a project within the given workspace."""
        self._assert_workspace_access(workspace_id, requesting_user_id)
        project = ProcurementProject(
            name=data.name,
            description=data.description,
            status=data.status,
            metadata_=data.metadata,
            workspace_id=workspace_id,
        )
        self._repo.create(project)
        self._db.commit()
        self._db.refresh(project)
        logger.info("Project '%s' created in workspace %s", project.name, workspace_id)
        return project

    def update_project(
        self,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        data: ProjectUpdate,
        requesting_user_id: uuid.UUID,
    ) -> ProcurementProject:
        """Partially update a project."""
        project = self.get_project(workspace_id, project_id, requesting_user_id)

        if data.name is not None:
            project.name = data.name
        if data.description is not None:
            project.description = data.description
        if data.status is not None:
            project.status = data.status
        if data.metadata is not None:
            project.metadata_ = data.metadata

        self._repo.update(project)
        self._db.commit()
        self._db.refresh(project)
        logger.info("Project %s updated", project_id)
        return project

    def delete_project(
        self, workspace_id: uuid.UUID, project_id: uuid.UUID, requesting_user_id: uuid.UUID
    ) -> None:
        """Soft-delete a project."""
        project = self.get_project(workspace_id, project_id, requesting_user_id)
        self._repo.soft_delete(project)
        self._db.commit()
        logger.info("Project %s soft-deleted", project_id)
