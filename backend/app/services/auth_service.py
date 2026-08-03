"""
Authentication service.

Orchestrates user registration, login, and token refresh.
Business logic only — no HTTP concerns, no direct DB access.
"""

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError, InactiveAccountError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest, TokenResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    """
    Handles authentication workflows: register, login, and token refresh.
    """

    def __init__(self, db: Session) -> None:
        self._repo = UserRepository(db)
        self._db = db

    def register(self, data: RegisterRequest) -> TokenResponse:
        """
        Register a new user and return tokens.

        Raises:
            ConflictError: If the email is already taken.
        """
        if self._repo.get_by_email(data.email):
            raise ConflictError(
                message=f"A user with email '{data.email}' already exists.",
                error_code="EMAIL_TAKEN",
            )

        user = User(
            email=data.email.lower().strip(),
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
        )
        self._repo.create(user)
        self._db.commit()
        self._db.refresh(user)

        logger.info("New user registered: %s", user.email)

        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )

    def login(self, email: str, password: str) -> TokenResponse:
        """
        Authenticate a user and return tokens.

        Raises:
            UnauthorizedError: If credentials are invalid.
            InactiveAccountError: If the account is suspended.
        """
        user = self._repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError(
                message="Invalid email or password",
                error_code="INVALID_CREDENTIALS",
            )
        if not user.is_active:
            raise InactiveAccountError()

        logger.info("User logged in: %s", user.email)

        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )

    def refresh(self, refresh_token: str) -> TokenResponse:
        """
        Exchange a valid refresh token for a new token pair.

        Raises:
            UnauthorizedError: If the refresh token is invalid or expired.
            NotFoundError: If the referenced user no longer exists.
            InactiveAccountError: If the account is suspended.
        """
        user_id_str = decode_refresh_token(refresh_token)

        import uuid
        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError as exc:
            raise UnauthorizedError("Malformed token subject") from exc

        user = self._repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        if not user.is_active:
            raise InactiveAccountError()

        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )
