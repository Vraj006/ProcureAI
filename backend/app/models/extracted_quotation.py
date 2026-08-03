"""
SQLAlchemy models for persisted extraction results.

Two tables:
  - extracted_quotations  (1:1 with quotations, holds all flat fields)
  - extracted_quotation_items  (1:N with extracted_quotations, one row per line-item)
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ExtractionStatus(str, enum.Enum):
    """Lifecycle status of an AI extraction attempt."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# ExtractedQuotation
# ---------------------------------------------------------------------------


class ExtractedQuotation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Flattened, AI-extracted procurement data for a single Quotation.

    One-to-one with the source Quotation record. All vendor, quotation
    header, pricing and commercial-term fields are stored as flat columns
    to allow direct SQL queries without JSON parsing.
    """

    __tablename__ = "extracted_quotations"

    # ── Source link ─────────────────────────────────────────────────────
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,           # enforces 1:1 with Quotation
        index=True,
        doc="FK to the source Quotation record",
    )

    # ── Vendor fields ────────────────────────────────────────────────────
    vendor_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    vendor_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    vendor_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    vendor_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vendor_gst_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ── Quotation header fields ──────────────────────────────────────────
    quotation_number: Mapped[str | None] = mapped_column(String(256), nullable=True)
    quotation_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    valid_until: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ── Pricing fields ───────────────────────────────────────────────────
    subtotal: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    discount: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    shipping_cost: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    tax: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    grand_total: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)

    # ── Commercial terms ─────────────────────────────────────────────────
    payment_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivery_time: Mapped[str | None] = mapped_column(String(256), nullable=True)
    warranty: Mapped[str | None] = mapped_column(String(512), nullable=True)
    incoterms: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ── Extraction metadata ──────────────────────────────────────────────
    extraction_status: Mapped[ExtractionStatus] = mapped_column(
        Enum(ExtractionStatus, name="extraction_status_enum"),
        nullable=False,
        default=ExtractionStatus.PENDING,
        server_default=ExtractionStatus.PENDING.value,
        index=True,
        doc="Current status of the AI extraction attempt",
    )
    extraction_model: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        doc="Name/version of the AI model used for extraction",
    )
    extracted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when extraction completed",
    )

    # ── Relationships ────────────────────────────────────────────────────
    quotation: Mapped["Quotation"] = relationship(  # noqa: F821
        "Quotation",
        back_populates="extracted_quotation",
        lazy="select",
    )
    items: Mapped[list["ExtractedQuotationItem"]] = relationship(
        "ExtractedQuotationItem",
        back_populates="extracted_quotation",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ExtractedQuotation id={self.id} "
            f"quotation_id={self.quotation_id} "
            f"status={self.extraction_status}>"
        )


# ---------------------------------------------------------------------------
# ExtractedQuotationItem
# ---------------------------------------------------------------------------


class ExtractedQuotationItem(UUIDPrimaryKeyMixin, Base):
    """
    A single line-item extracted from an AI-parsed procurement quotation.

    Many-to-one with ExtractedQuotation.
    """

    __tablename__ = "extracted_quotation_items"

    extracted_quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extracted_quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to the parent ExtractedQuotation",
    )

    item_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit_price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    total_price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)

    extracted_quotation: Mapped["ExtractedQuotation"] = relationship(
        "ExtractedQuotation",
        back_populates="items",
        lazy="select",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ExtractedQuotationItem id={self.id} "
            f"name={self.item_name!r} qty={self.quantity}>"
        )
