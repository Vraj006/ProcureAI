"""
Vendor CRUD routes.

All routes scoped to /api/v1/workspaces/{workspace_id}/vendors/
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.vendor import (
    PaginatedVendorResponse,
    VendorCreate,
    VendorResponse,
    VendorUpdate,
)
from app.services.vendor_service import VendorService

router = APIRouter(prefix="/workspaces/{workspace_id}/vendors", tags=["Vendors"])


@router.post(
    "/",
    response_model=VendorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create vendor",
)
def create_vendor(
    workspace_id: uuid.UUID,
    data: VendorCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> VendorResponse:
    """Add a new vendor to a workspace."""
    vendor = VendorService(db).create_vendor(workspace_id, data, current_user.id)
    return VendorResponse.model_validate(vendor)


@router.get(
    "/",
    response_model=PaginatedVendorResponse,
    summary="List vendors",
)
def list_vendors(
    workspace_id: uuid.UUID,
    search: str | None = Query(None, description="Search by company name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PaginatedVendorResponse:
    """List vendors in a workspace with optional company name search and pagination."""
    return VendorService(db).list_vendors(
        workspace_id, current_user.id, search=search, page=page, page_size=page_size
    )


@router.get(
    "/{vendor_id}",
    response_model=VendorResponse,
    summary="Get vendor",
)
def get_vendor(
    workspace_id: uuid.UUID,
    vendor_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> VendorResponse:
    """Get a specific vendor by ID."""
    vendor = VendorService(db).get_vendor(workspace_id, vendor_id, current_user.id)
    return VendorResponse.model_validate(vendor)


@router.put(
    "/{vendor_id}",
    response_model=VendorResponse,
    summary="Update vendor",
)
def update_vendor(
    workspace_id: uuid.UUID,
    vendor_id: uuid.UUID,
    data: VendorUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> VendorResponse:
    """Partially update a vendor."""
    vendor = VendorService(db).update_vendor(workspace_id, vendor_id, data, current_user.id)
    return VendorResponse.model_validate(vendor)


@router.delete(
    "/{vendor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete vendor",
)
def delete_vendor(
    workspace_id: uuid.UUID,
    vendor_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """Soft-delete a vendor."""
    VendorService(db).delete_vendor(workspace_id, vendor_id, current_user.id)
