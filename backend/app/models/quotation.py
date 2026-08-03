"""
Quotation SQLAlchemy model.

A quotation is a vendor's price offer for a procurement project.
It links a Vendor to a ProcurementProject, and tracks the uploaded
document and its processing lifecycle.
"""

import enum
import uuid
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class QuotationStatus(str, enum.Enum):
    """
    Lifecycle state of a quotation.

    - ``pending``    : Record created; awaiting file upload.
    - ``uploaded``   : File uploaded successfully; ready for AI processing.
    - ``processing`` : AI agents are parsing / extracting data.
    - ``processed``  : Extraction complete; data available for comparison.
    - ``failed``     : Processing encountered an unrecoverable error.
    - ``rejected``   : Manually rejected by a team member.
    """

    PENDING = "pending"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    REJECTED = "rejected"


class Quotation(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """
    A vendor's price offer for a specific procurement project.

    Stores both the business metadata (amount, currency, date) and the
    uploaded document details (file_path, mime_type, file_size).
    """

    __tablename__ = "quotations"

    # Core references
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("procurement_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Procurement project this quotation was submitted for",
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Vendor who submitted this quotation",
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        doc="User who uploaded the quotation",
    )

    # Business fields
    quotation_number: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        doc="Vendor-assigned quotation reference number",
    )
    quotation_date: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Date on the quotation document (ISO 8601 string: YYYY-MM-DD)",
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="USD",
        doc="ISO 4217 currency code (e.g. USD, EUR, INR)",
    )
    total_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=True,
        doc="Total quoted amount in the stated currency",
    )
    status: Mapped[QuotationStatus] = mapped_column(
        Enum(QuotationStatus, name="quotationstatus"),
        default=QuotationStatus.PENDING,
        nullable=False,
        index=True,
        doc="Current lifecycle state of the quotation",
    )

    # File metadata (populated after upload)
    file_name: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        doc="Original filename as uploaded",
    )
    file_path: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
        doc="Relative path from upload base directory",
    )
    mime_type: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        doc="MIME type of the uploaded file",
    )
    file_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="File size in bytes",
    )

    # Relationships
    project: Mapped["ProcurementProject"] = relationship(  # noqa: F821
        "ProcurementProject",
        back_populates="quotations",
        lazy="select",
    )
    vendor: Mapped["Vendor"] = relationship(  # noqa: F821
        "Vendor",
        back_populates="quotations",
        lazy="select",
    )
    uploaded_by_user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        foreign_keys=[uploaded_by],
        lazy="select",
    )
    extracted_quotation: Mapped["ExtractedQuotation | None"] = relationship(  # noqa: F821
        "ExtractedQuotation",
        back_populates="quotation",
        uselist=False,          # 1:1 — one extraction per quotation
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Quotation id={self.id} number={self.quotation_number!r} "
            f"status={self.status} vendor_id={self.vendor_id}>"
        )
