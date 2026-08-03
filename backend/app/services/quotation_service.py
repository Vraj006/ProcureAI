"""
Quotation service.

Orchestrates quotation lifecycle: creation, file upload, CRUD, and status tracking.
Validates vendor membership, duplicate quotation numbers, and file integrity.
"""

import math
import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.quotation import Quotation, QuotationStatus
from app.repositories.project_repository import ProjectRepository
from app.repositories.quotation_repository import QuotationRepository
from app.repositories.vendor_repository import VendorRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.quotation import (
    PaginatedQuotationResponse,
    QuotationCreate,
    QuotationResponse,
    QuotationUpdate,
    UploadResponse,
)
from app.services.storage_service import StorageService
from app.utils.file_validators import validate_upload_file

logger = get_logger(__name__)


class QuotationService:
    """
    Manages quotation lifecycle within procurement projects.

    Validates:
    - Workspace ownership
    - Project membership
    - Vendor membership in workspace
    - Duplicate quotation numbers (per project)
    - File type, size, and emptiness
    """

    def __init__(self, db: Session, storage: StorageService) -> None:
        self._repo = QuotationRepository(db)
        self._project_repo = ProjectRepository(db)
        self._vendor_repo = VendorRepository(db)
        self._ws_repo = WorkspaceRepository(db)
        self._storage = storage
        self._db = db

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _invalidate_project_analysis(self, project_id: uuid.UUID) -> None:
        """Clear cached AI analysis results to prevent stale data display."""
        project = self._project_repo.get_by_id(project_id)
        if project and project.metadata_:
            meta = dict(project.metadata_)
            dirty = False
            for key in ["comparison", "compliance", "recommendation"]:
                if key in meta:
                    del meta[key]
                    dirty = True
            if dirty:
                project.metadata_ = meta
                self._project_repo.update(project)

    def _assert_workspace_access(
        self, workspace_id: uuid.UUID, requesting_user_id: uuid.UUID
    ) -> None:
        ws = self._ws_repo.get_by_id(workspace_id)
        if not ws:
            raise NotFoundError(message=f"Workspace {workspace_id} not found")
        if ws.owner_id != requesting_user_id:
            raise ForbiddenError()

    def _assert_project_in_workspace(
        self, project_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> None:
        project = self._project_repo.get_by_id(project_id)
        if not project or project.workspace_id != workspace_id:
            raise NotFoundError(
                message=f"Project {project_id} not found in workspace {workspace_id}"
            )

    def _assert_vendor_in_workspace(
        self, vendor_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> None:
        vendor = self._vendor_repo.get_by_id_in_workspace(vendor_id, workspace_id)
        if not vendor:
            raise NotFoundError(
                message=f"Vendor {vendor_id} not found in workspace {workspace_id}"
            )

    def _get_quotation(
        self, quotation_id: uuid.UUID, project_id: uuid.UUID
    ) -> Quotation:
        q = self._repo.get_by_id_in_project(quotation_id, project_id)
        if not q:
            raise NotFoundError(
                message=f"Quotation {quotation_id} not found in project {project_id}"
            )
        return q

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def list_quotations(
        self,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        requesting_user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedQuotationResponse:
        self._assert_workspace_access(workspace_id, requesting_user_id)
        self._assert_project_in_workspace(project_id, workspace_id)

        items, total = self._repo.list_by_project(project_id, page=page, page_size=page_size)
        pages = math.ceil(total / page_size) if page_size else 1
        return PaginatedQuotationResponse(
            items=[QuotationResponse.model_validate(q) for q in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_quotation(
        self,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        quotation_id: uuid.UUID,
        requesting_user_id: uuid.UUID,
    ) -> Quotation:
        self._assert_workspace_access(workspace_id, requesting_user_id)
        self._assert_project_in_workspace(project_id, workspace_id)
        return self._get_quotation(quotation_id, project_id)

    def create_quotation(
        self,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        data: QuotationCreate,
        requesting_user_id: uuid.UUID,
    ) -> Quotation:
        """
        Create a quotation record (metadata only — file is uploaded separately).

        Raises:
            ConflictError: If the quotation number already exists in this project.
            NotFoundError: If vendor is not in this workspace.
        """
        self._assert_workspace_access(workspace_id, requesting_user_id)
        self._assert_project_in_workspace(project_id, workspace_id)
        self._assert_vendor_in_workspace(data.vendor_id, workspace_id)

        # Duplicate number check
        if self._repo.get_by_number_in_project(data.quotation_number, project_id):
            raise ConflictError(
                message=f"Quotation number '{data.quotation_number}' already exists in this project.",
                error_code="DUPLICATE_QUOTATION_NUMBER",
            )

        quotation = Quotation(
            project_id=project_id,
            vendor_id=data.vendor_id,
            uploaded_by=requesting_user_id,
            quotation_number=data.quotation_number,
            quotation_date=data.quotation_date,
            currency=data.currency,
            total_amount=data.total_amount,
            status=data.status,
        )
        self._repo.create(quotation)
        self._db.commit()
        self._db.refresh(quotation)
        logger.info(
            "Quotation '%s' created for project %s", data.quotation_number, project_id
        )
        return quotation

    def update_quotation(
        self,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        quotation_id: uuid.UUID,
        data: QuotationUpdate,
        requesting_user_id: uuid.UUID,
    ) -> Quotation:
        self._assert_workspace_access(workspace_id, requesting_user_id)
        self._assert_project_in_workspace(project_id, workspace_id)
        quotation = self._get_quotation(quotation_id, project_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(quotation, field, value)

        self._repo.update(quotation)
        self._db.commit()
        self._db.refresh(quotation)
        
        self._invalidate_project_analysis(project_id)
        self._db.commit()
        
        logger.info("Quotation %s updated", quotation_id)
        return quotation

    def delete_quotation(
        self,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        quotation_id: uuid.UUID,
        requesting_user_id: uuid.UUID,
    ) -> None:
        self._assert_workspace_access(workspace_id, requesting_user_id)
        self._assert_project_in_workspace(project_id, workspace_id)
        quotation = self._get_quotation(quotation_id, project_id)

        # Delete file if present
        if quotation.file_path:
            try:
                self._storage.delete_file(quotation.file_path)
            except Exception as exc:
                logger.warning("Could not delete file during quotation delete: %s", exc)

        self._repo.soft_delete(quotation)
        self._db.commit()
        
        self._invalidate_project_analysis(project_id)
        self._db.commit()
        
        logger.info("Quotation %s soft-deleted", quotation_id)

    # ------------------------------------------------------------------
    # File upload
    # ------------------------------------------------------------------

    async def upload_file(
        self,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        quotation_id: uuid.UUID,
        file: UploadFile,
        requesting_user_id: uuid.UUID,
    ) -> UploadResponse:
        """
        Validate and store a quotation document.

        Validates file type (.pdf/.docx/.xlsx), size, and emptiness.
        Updates quotation status to UPLOADED on success, FAILED on error.

        Raises:
            ValidationError: For invalid file type, empty file, or size limit exceeded.
        """
        self._assert_workspace_access(workspace_id, requesting_user_id)
        self._assert_project_in_workspace(project_id, workspace_id)
        quotation = self._get_quotation(quotation_id, project_id)

        max_bytes = settings.max_upload_size_mb * 1024 * 1024

        try:
            content = await validate_upload_file(file, max_bytes)
        except ValidationError:
            quotation.status = QuotationStatus.FAILED
            self._repo.update(quotation)
            self._db.commit()
            logger.warning(
                "File upload validation failed for quotation %s", quotation_id
            )
            raise

        try:
            stored = self._storage.save_file(
                workspace_id=workspace_id,
                project_id=project_id,
                quotation_id=quotation_id,
                file_name=file.filename or "upload",
                content=content,
            )

            quotation.file_name = stored.file_name
            quotation.file_path = stored.file_path
            quotation.file_size = stored.file_size
            quotation.mime_type = stored.mime_type
            quotation.status = QuotationStatus.UPLOADED

            self._repo.update(quotation)
            self._db.commit()
            self._db.refresh(quotation)

            self._invalidate_project_analysis(project_id)
            self._db.commit()

            logger.info(
                "Quotation %s file uploaded: %s (%.1f KB)",
                quotation_id,
                stored.file_name,
                stored.file_size / 1024,
            )

            return UploadResponse(
                quotation_id=quotation.id,
                file_name=stored.file_name,
                file_size=stored.file_size,
                mime_type=stored.mime_type,
                status=QuotationStatus.UPLOADED,
            )

        except Exception as exc:
            quotation.status = QuotationStatus.FAILED
            self._repo.update(quotation)
            self._db.commit()
            logger.error("File save failed for quotation %s: %s", quotation_id, exc)
            raise
