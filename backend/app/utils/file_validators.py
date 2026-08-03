"""
File validation utilities.

Validates uploaded files for type, size, and content integrity
before they are passed to the storage service.
"""

from fastapi import UploadFile

from app.core.exceptions import ValidationError

# ---------------------------------------------------------------------------
# Allowed types
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".docx", ".xlsx"})

ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        # Some browsers send these for docx/xlsx
        "application/msword",
        "application/vnd.ms-excel",
        "application/octet-stream",  # fallback when browser can't detect
    }
)

EXTENSION_TO_MIME: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


# ---------------------------------------------------------------------------
# Public validator
# ---------------------------------------------------------------------------


async def validate_upload_file(file: UploadFile, max_size_bytes: int) -> bytes:
    """
    Validate an uploaded file and return its raw bytes.

    Checks:
    - File extension is allowed (.pdf, .docx, .xlsx)
    - File is not empty
    - File size does not exceed max_size_bytes

    Args:
        file: The FastAPI UploadFile object.
        max_size_bytes: Maximum allowed file size in bytes.

    Returns:
        Raw file content as bytes.

    Raises:
        ValidationError: If any validation rule is violated.
    """
    # Check extension
    filename = file.filename or ""
    suffix = _get_extension(filename)
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            message=(
                f"File type '{suffix or 'unknown'}' is not allowed. "
                f"Permitted types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
            error_code="INVALID_FILE_TYPE",
        )

    # Read content
    content = await file.read()
    await file.seek(0)  # reset so callers can re-read if needed

    # Check not empty
    if len(content) == 0:
        raise ValidationError(
            message="Uploaded file is empty.",
            error_code="EMPTY_FILE",
        )

    # Check size
    if len(content) > max_size_bytes:
        max_mb = max_size_bytes / (1024 * 1024)
        actual_mb = len(content) / (1024 * 1024)
        raise ValidationError(
            message=(
                f"File size {actual_mb:.1f} MB exceeds the maximum allowed "
                f"size of {max_mb:.0f} MB."
            ),
            error_code="FILE_TOO_LARGE",
        )

    return content


def _get_extension(filename: str) -> str:
    """Return the lowercased file extension including the dot, e.g. '.pdf'."""
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()
