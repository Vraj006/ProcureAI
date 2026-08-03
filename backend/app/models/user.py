"""
User SQLAlchemy model.

Represents a registered user of the ProcureAI platform.
Passwords are stored as bcrypt hashes — never in plain text.
"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """
    Platform user.

    Owns one or more workspaces; authenticates via email + password.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
        doc="User's email address — used as the login identifier",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        doc="bcrypt hash of the user's password",
    )
    full_name: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        doc="User's display name",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        doc="When False, the account is suspended and login is denied",
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        doc="When True, grants administrative privileges",
    )

    # Relationships
    workspaces: Mapped[list["Workspace"]] = relationship(  # noqa: F821
        "Workspace",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email!r}>"
