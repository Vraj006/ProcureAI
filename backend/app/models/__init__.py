"""
ORM model registry.

All SQLAlchemy models must be imported here so that Alembic's autogenerate
can detect table definitions via Base.metadata. Import order respects
foreign-key dependencies.
"""

from app.models.user import User  # noqa: F401
from app.models.workspace import Workspace  # noqa: F401
from app.models.project import ProcurementProject, ProjectStatus  # noqa: F401
from app.models.vendor import Vendor  # noqa: F401
from app.models.quotation import Quotation, QuotationStatus  # noqa: F401
from app.models.extracted_quotation import (  # noqa: F401
    ExtractedQuotation,
    ExtractedQuotationItem,
    ExtractionStatus,
)

__all__ = [
    "User",
    "Workspace",
    "ProcurementProject",
    "ProjectStatus",
    "Vendor",
    "Quotation",
    "QuotationStatus",
    "ExtractedQuotation",
    "ExtractedQuotationItem",
    "ExtractionStatus",
]
