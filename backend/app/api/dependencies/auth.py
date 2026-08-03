"""
Authentication dependency.

Provides get_current_user and get_current_active_user as FastAPI
injectable dependencies for protecting routes.
"""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import InactiveAccountError, UnauthorizedError
from app.core.security import decode_access_token
from app.database.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

import uuid

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency — extract and validate the Bearer token, return User.

    Raises:
        UnauthorizedError: If no token is provided, or it is invalid/expired.
        UnauthorizedError: If the user referenced by the token no longer exists.
    """
    if credentials is None:
        raise UnauthorizedError("Bearer token required")

    user_id_str = decode_access_token(credentials.credentials)

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError as exc:
        raise UnauthorizedError("Malformed token subject") from exc

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("User not found")

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    FastAPI dependency — like get_current_user but also rejects inactive accounts.

    Raises:
        InactiveAccountError: If the account is suspended.
    """
    if not current_user.is_active:
        raise InactiveAccountError()
    return current_user
