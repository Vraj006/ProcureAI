"""Procurement Project CRUD routes with search and pagination."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.project import (
    PaginatedProjectResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project_service import ProjectService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/projects",
    tags=["Projects"],
)


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
)
def create_project(
    workspace_id: uuid.UUID,
    data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Create a procurement project inside the given workspace."""
    project = ProjectService(db).create_project(workspace_id, data, current_user.id)
    return ProjectResponse.model_validate(project)


@router.get(
    "/",
    response_model=PaginatedProjectResponse,
    summary="List projects",
)
def list_projects(
    workspace_id: uuid.UUID,
    search: str | None = Query(None, description="Substring search on name or description"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PaginatedProjectResponse:
    """Return a paginated list of projects in the workspace, with optional search."""
    return ProjectService(db).list_projects(
        workspace_id, current_user.id, search=search, page=page, page_size=page_size
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project",
)
def get_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Get a single project by ID."""
    project = ProjectService(db).get_project(workspace_id, project_id, current_user.id)
    return ProjectResponse.model_validate(project)


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
)
def update_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Partially update a project."""
    project = ProjectService(db).update_project(workspace_id, project_id, data, current_user.id)
    return ProjectResponse.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
)
def delete_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """Soft-delete a project."""
    ProjectService(db).delete_project(workspace_id, project_id, current_user.id)
