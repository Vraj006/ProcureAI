"""Workspace CRUD routes."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.post(
    "/",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create workspace",
)
def create_workspace(
    data: WorkspaceCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WorkspaceResponse:
    """Create a new workspace owned by the current user."""
    ws = WorkspaceService(db).create_workspace(data, current_user.id)
    return WorkspaceResponse.model_validate(ws)


@router.get(
    "/",
    response_model=list[WorkspaceResponse],
    summary="List my workspaces",
)
def list_workspaces(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[WorkspaceResponse]:
    """Return all workspaces owned by the current user."""
    workspaces = WorkspaceService(db).list_workspaces(current_user.id)
    return [WorkspaceResponse.model_validate(ws) for ws in workspaces]


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Get workspace",
)
def get_workspace(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WorkspaceResponse:
    """Get a specific workspace (must be the owner)."""
    ws = WorkspaceService(db).get_workspace(workspace_id, current_user.id)
    return WorkspaceResponse.model_validate(ws)


@router.put(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Update workspace",
)
def update_workspace(
    workspace_id: uuid.UUID,
    data: WorkspaceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WorkspaceResponse:
    """Partially update a workspace (must be the owner)."""
    ws = WorkspaceService(db).update_workspace(workspace_id, data, current_user.id)
    return WorkspaceResponse.model_validate(ws)


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete workspace",
)
def delete_workspace(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """Soft-delete a workspace (must be the owner)."""
    WorkspaceService(db).delete_workspace(workspace_id, current_user.id)
