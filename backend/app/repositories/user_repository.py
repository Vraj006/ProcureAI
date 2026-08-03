"""
User repository.

Encapsulates all database access for User records using SQLAlchemy 2.x
select() style — no legacy Query API.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """
    Data-access object for the User model.

    All methods filter out soft-deleted records by default.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Return an active user by primary key, or None."""
        stmt = select(User).where(User.id == user_id, User.is_deleted.is_(False))
        return self._db.scalars(stmt).first()

    def get_by_email(self, email: str) -> User | None:
        """Return an active user by email address (case-insensitive), or None."""
        stmt = select(User).where(
            User.email == email.lower().strip(),
            User.is_deleted.is_(False),
        )
        return self._db.scalars(stmt).first()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, user: User) -> User:
        """Persist a new User instance and return it after flush."""
        self._db.add(user)
        self._db.flush()
        self._db.refresh(user)
        return user

    def update(self, user: User) -> User:
        """Flush pending changes for an already-tracked User and return it."""
        self._db.flush()
        self._db.refresh(user)
        return user

    def soft_delete(self, user: User) -> None:
        """Mark a user as deleted (sets is_deleted=True)."""
        user.is_deleted = True
        self._db.flush()
