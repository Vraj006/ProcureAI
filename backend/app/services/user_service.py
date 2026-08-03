"""
User service.

Business logic for managing user accounts.
Delegates all DB access to UserRepository.
"""

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.security import hash_password
from app.core.logging import get_logger
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdate

logger = get_logger(__name__)


class UserService:
    """Handles user profile management operations."""

    def __init__(self, db: Session) -> None:
        self._repo = UserRepository(db)
        self._db = db

    def get_user(self, user_id: uuid.UUID):
        """
        Retrieve an active user by ID.

        Raises:
            NotFoundError: If the user does not exist or has been soft-deleted.
        """
        user = self._repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(message=f"User {user_id} not found")
        return user

    def update_user(self, user_id: uuid.UUID, data: UserUpdate):
        """
        Apply partial updates to a user profile.

        Only provided (non-None) fields are applied.

        Raises:
            NotFoundError: If the user does not exist.
        """
        user = self.get_user(user_id)

        if data.full_name is not None:
            user.full_name = data.full_name
        if data.password is not None:
            user.hashed_password = hash_password(data.password)

        self._repo.update(user)
        self._db.commit()
        self._db.refresh(user)

        logger.info("User %s profile updated", user_id)
        return user

    def delete_user(self, user_id: uuid.UUID) -> None:
        """
        Soft-delete a user account.

        Raises:
            NotFoundError: If the user does not exist.
        """
        user = self.get_user(user_id)
        self._repo.soft_delete(user)
        self._db.commit()
        logger.info("User %s soft-deleted", user_id)
