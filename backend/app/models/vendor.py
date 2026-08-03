"""
Vendor SQLAlchemy model.

A vendor represents a supplier company that submits quotations
within a workspace. One workspace can have many vendors.
"""

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from sqlalchemy import ForeignKey
from app.database.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Vendor(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """
    Supplier profile within a workspace.

    Belongs to a Workspace; has many Quotations (via projects).
    """

    __tablename__ = "vendors"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Owning workspace",
    )
    company_name: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        index=True,
        doc="Legal company name of the vendor",
    )
    contact_person: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        doc="Primary contact person's name",
    )
    email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
        doc="Vendor contact email address",
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Vendor contact phone number",
    )
    website: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        doc="Vendor website URL",
    )
    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Full postal address",
    )
    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Country of operation",
    )
    tax_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="GST / Tax identification number (optional)",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Free-form internal notes about this vendor",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        doc="When False, vendor is archived and excluded from new quotations",
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship(  # noqa: F821
        "Workspace",
        back_populates="vendors",
        lazy="select",
    )
    quotations: Mapped[list["Quotation"]] = relationship(  # noqa: F821
        "Quotation",
        back_populates="vendor",
        lazy="select",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Vendor id={self.id} company={self.company_name!r}>"
