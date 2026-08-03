"""
Storage service.

Abstracts all file I/O for the application. The rest of the code should
NEVER manipulate files directly — always go through this service.

Designed for easy migration to cloud storage (S3, Azure Blob) in the future:
replace only this module, nothing else touches file paths.
"""

import uuid
from dataclasses import dataclass
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class StoredFile:
    """
    Metadata returned after successfully persisting an uploaded file.

    Attributes:
        file_name: The original filename as uploaded by the user.
        file_path: Relative path from the upload base directory.
        file_size: Size in bytes.
        mime_type: Detected MIME type based on extension.
    """

    file_name: str
    file_path: str
    file_size: int
    mime_type: str


_EXTENSION_TO_MIME: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


class StorageService:
    """
    Local filesystem storage service.

    Files are stored under:
        <base_dir>/<workspace_id>/<project_id>/<quotation_id>/<original_filename>

    Replace this class (keeping the same interface) to switch to S3, Azure, GCS, etc.
    """

    def __init__(self, base_dir: Path) -> None:
        """
        Args:
            base_dir: Absolute path to the root upload directory.
        """
        self._base = base_dir
        self._base.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def save_file(
        self,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        quotation_id: uuid.UUID,
        file_name: str,
        content: bytes,
    ) -> StoredFile:
        """
        Persist raw file bytes to disk and return metadata.

        Args:
            workspace_id: Owning workspace (used for folder partitioning).
            project_id: Owning project.
            quotation_id: Owning quotation.
            file_name: Original filename (used as the stored filename).
            content: Raw file bytes to write.

        Returns:
            StoredFile metadata for persistence in the database.
        """
        dest_dir = self._base / str(workspace_id) / str(project_id) / str(quotation_id)
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest_path = dest_dir / file_name
        dest_path.write_bytes(content)

        relative_path = str(dest_path.relative_to(self._base))
        extension = self._get_extension(file_name)
        mime_type = _EXTENSION_TO_MIME.get(extension, "application/octet-stream")

        logger.info(
            "File saved: %s (%.1f KB) → %s",
            file_name,
            len(content) / 1024,
            relative_path,
        )

        return StoredFile(
            file_name=file_name,
            file_path=relative_path,
            file_size=len(content),
            mime_type=mime_type,
        )

    def delete_file(self, file_path: str) -> None:
        """
        Remove a stored file from disk.

        Args:
            file_path: Relative path as stored in the database.
        """
        abs_path = self._base / file_path
        if abs_path.exists():
            abs_path.unlink()
            logger.info("File deleted: %s", file_path)
        else:
            logger.warning("File not found for deletion: %s", file_path)

    def get_absolute_path(self, file_path: str) -> Path:
        """
        Resolve a stored relative path to an absolute filesystem path.

        Args:
            file_path: Relative path as stored in the database.

        Returns:
            Absolute Path object.
        """
        return self._base / file_path

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_extension(file_name: str) -> str:
        if "." not in file_name:
            return ""
        return "." + file_name.rsplit(".", 1)[-1].lower()


# ---------------------------------------------------------------------------
# Dependency-injectable factory
# ---------------------------------------------------------------------------


def get_storage_service() -> StorageService:
    """
    FastAPI dependency that returns a configured StorageService instance.

    Reads upload_dir from settings and resolves it relative to the
    backend root directory.
    """
    from pathlib import Path
    from app.core.config import settings

    # Resolve relative to backend/ (one level above app/)
    backend_root = Path(__file__).resolve().parent.parent.parent
    base_dir = backend_root / settings.upload_dir
    return StorageService(base_dir=base_dir)
