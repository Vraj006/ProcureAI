"""
Quotation CRUD and file upload routes.

Scoped to /api/v1/workspaces/{workspace_id}/projects/{project_id}/quotations/
"""

import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.quotation import (
    PaginatedQuotationResponse,
    QuotationCreate,
    QuotationResponse,
    QuotationUpdate,
    UploadResponse,
)
from app.services.quotation_service import QuotationService
from app.services.storage_service import StorageService, get_storage_service

router = APIRouter(
    prefix="/workspaces/{workspace_id}/projects/{project_id}/quotations",
    tags=["Quotations"],
)


@router.post(
    "/",
    response_model=QuotationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create quotation",
    description=(
        "Create a quotation record with metadata. "
        "Upload the actual document using POST /{quotation_id}/upload."
    ),
)
def create_quotation(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    data: QuotationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> QuotationResponse:
    quotation = QuotationService(db, storage).create_quotation(
        workspace_id, project_id, data, current_user.id
    )
    return QuotationResponse.model_validate(quotation)


@router.get(
    "/",
    response_model=PaginatedQuotationResponse,
    summary="List quotations",
)
def list_quotations(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> PaginatedQuotationResponse:
    """List all quotations for a project with pagination."""
    return QuotationService(db, storage).list_quotations(
        workspace_id, project_id, current_user.id, page=page, page_size=page_size
    )


@router.get(
    "/{quotation_id}",
    response_model=QuotationResponse,
    summary="Get quotation",
)
def get_quotation(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    quotation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> QuotationResponse:
    quotation = QuotationService(db, storage).get_quotation(
        workspace_id, project_id, quotation_id, current_user.id
    )
    return QuotationResponse.model_validate(quotation)


@router.put(
    "/{quotation_id}",
    response_model=QuotationResponse,
    summary="Update quotation",
)
def update_quotation(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    quotation_id: uuid.UUID,
    data: QuotationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> QuotationResponse:
    """Partially update a quotation's metadata or status."""
    quotation = QuotationService(db, storage).update_quotation(
        workspace_id, project_id, quotation_id, data, current_user.id
    )
    return QuotationResponse.model_validate(quotation)


@router.delete(
    "/{quotation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete quotation",
)
def delete_quotation(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    quotation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> None:
    """Soft-delete a quotation and remove its uploaded file."""
    QuotationService(db, storage).delete_quotation(
        workspace_id, project_id, quotation_id, current_user.id
    )


@router.post(
    "/{quotation_id}/upload",
    response_model=UploadResponse,
    summary="Upload quotation document",
    description=(
        "Upload a PDF, DOCX, or XLSX quotation document. "
        "Max size is configurable (default 10 MB). "
        "On success the quotation status changes from `pending` → `uploaded`."
    ),
)
async def upload_quotation_file(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    quotation_id: uuid.UUID,
    file: UploadFile = File(
        ...,
        description="Quotation document — accepted formats: .pdf, .docx, .xlsx",
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> UploadResponse:
    """
    Upload the actual quotation document.

    - Validates file type (PDF / DOCX / XLSX)
    - Validates file is not empty
    - Validates file size does not exceed the configured limit
    - Stores the file at uploads/{workspace_id}/{project_id}/{quotation_id}/{filename}
    - Updates quotation status to `uploaded` (or `failed` on error)
    """
    return await QuotationService(db, storage).upload_file(
        workspace_id, project_id, quotation_id, file, current_user.id
    )
