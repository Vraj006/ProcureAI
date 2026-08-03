"""
Vendor service.

Business logic for vendor management.
Enforces workspace ownership on all mutating operations.
"""

import math
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.models.vendor import Vendor
from app.repositories.vendor_repository import VendorRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.vendor import PaginatedVendorResponse, VendorCreate, VendorResponse, VendorUpdate

logger = get_logger(__name__)


class VendorService:
    """Manages vendor lifecycle with workspace ownership enforcement."""

    def __init__(self, db: Session) -> None:
        self._repo = VendorRepository(db)
        self._ws_repo = WorkspaceRepository(db)
        self._db = db

    def _assert_workspace_access(
        self, workspace_id: uuid.UUID, requesting_user_id: uuid.UUID
    ) -> None:
        ws = self._ws_repo.get_by_id(workspace_id)
        if not ws:
            raise NotFoundError(message=f"Workspace {workspace_id} not found")
        if ws.owner_id != requesting_user_id:
            raise ForbiddenError()

    def get_vendor(
        self, workspace_id: uuid.UUID, vendor_id: uuid.UUID, requesting_user_id: uuid.UUID
    ) -> Vendor:
        """Retrieve a vendor, confirming workspace access."""
        self._assert_workspace_access(workspace_id, requesting_user_id)
        vendor = self._repo.get_by_id_in_workspace(vendor_id, workspace_id)
        if not vendor:
            raise NotFoundError(message=f"Vendor {vendor_id} not found")
        return vendor

    def list_vendors(
        self,
        workspace_id: uuid.UUID,
        requesting_user_id: uuid.UUID,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedVendorResponse:
        """Return a paginated, searchable list of vendors in a workspace."""
        self._assert_workspace_access(workspace_id, requesting_user_id)
        items, total = self._repo.list_by_workspace(
            workspace_id, search=search, page=page, page_size=page_size
        )
        pages = math.ceil(total / page_size) if page_size else 1
        return PaginatedVendorResponse(
            items=[VendorResponse.model_validate(v) for v in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def create_vendor(
        self, workspace_id: uuid.UUID, data: VendorCreate, requesting_user_id: uuid.UUID
    ) -> Vendor:
        """Create a vendor in the given workspace."""
        self._assert_workspace_access(workspace_id, requesting_user_id)
        vendor = Vendor(
            workspace_id=workspace_id,
            company_name=data.company_name,
            contact_person=data.contact_person,
            email=str(data.email) if data.email else None,
            phone=data.phone,
            website=data.website,
            address=data.address,
            country=data.country,
            tax_number=data.tax_number,
            notes=data.notes,
            is_active=data.is_active,
        )
        self._repo.create(vendor)
        self._db.commit()
        self._db.refresh(vendor)
        logger.info("Vendor '%s' created in workspace %s", vendor.company_name, workspace_id)
        return vendor

    def update_vendor(
        self,
        workspace_id: uuid.UUID,
        vendor_id: uuid.UUID,
        data: VendorUpdate,
        requesting_user_id: uuid.UUID,
    ) -> Vendor:
        """Partially update a vendor."""
        vendor = self.get_vendor(workspace_id, vendor_id, requesting_user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(vendor, field, value)
        self._repo.update(vendor)
        self._db.commit()
        self._db.refresh(vendor)
        logger.info("Vendor %s updated", vendor_id)
        return vendor

    def delete_vendor(
        self, workspace_id: uuid.UUID, vendor_id: uuid.UUID, requesting_user_id: uuid.UUID
    ) -> None:
        """Soft-delete a vendor."""
        vendor = self.get_vendor(workspace_id, vendor_id, requesting_user_id)
        self._repo.soft_delete(vendor)
        self._db.commit()
        logger.info("Vendor %s soft-deleted", vendor_id)
