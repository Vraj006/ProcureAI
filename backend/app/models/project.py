"""
Procurement Project SQLAlchemy model.

A project represents a single procurement cycle — collecting vendor quotations
for a specific requirement — and lives within a Workspace.
"""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ProjectStatus(str, enum.Enum):
    """
    Lifecycle states for a procurement project.

    - ``draft``    : Project is being set up; not yet active.
    - ``active``   : Quotations are being collected and analysed.
    - ``closed``   : Procurement decision has been made.
    - ``archived`` : Closed project retained for audit purposes.
    """

    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class ProcurementProject(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """
    A single procurement cycle within a Workspace.

    Holds metadata describing the requirement and tracks the project
    through its lifecycle states.
    """

    __tablename__ = "procurement_projects"

    name: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        index=True,
        doc="Project title / short name",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Detailed description of the procurement requirement",
    )
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="projectstatus"),
        default=ProjectStatus.DRAFT,
        nullable=False,
        index=True,
        doc="Current lifecycle state of the project",
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
        doc="Arbitrary JSON metadata (budget, category, tags, etc.)",
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to the owning Workspace",
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship(  # noqa: F821
        "Workspace",
        back_populates="projects",
        lazy="select",
    )
    quotations: Mapped[list["Quotation"]] = relationship(  # noqa: F821
        "Quotation",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ProcurementProject id={self.id} name={self.name!r} "
            f"status={self.status} workspace_id={self.workspace_id}>"
        )
