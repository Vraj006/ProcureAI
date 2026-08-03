"""
Workspace SQLAlchemy model.

A workspace groups related procurement projects and belongs to one owner (User).
Each user can own multiple workspaces.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Workspace(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """
    Organisational container for procurement projects.

    Owned by a single User; contains zero or more ProcurementProjects.
    """

    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        doc="Workspace display name",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Optional free-text description of the workspace",
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to the owning User",
    )

    # Relationships
    owner: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="workspaces",
        lazy="select",
    )
    projects: Mapped[list["ProcurementProject"]] = relationship(  # noqa: F821
        "ProcurementProject",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="select",
    )
    vendors: Mapped[list["Vendor"]] = relationship(  # noqa: F821
        "Vendor",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Workspace id={self.id} name={self.name!r} owner_id={self.owner_id}>"
