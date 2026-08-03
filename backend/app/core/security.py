"""
Security utilities for ProcureAI.

Uses bcrypt directly (avoids passlib/bcrypt 4.x+ compatibility issues).
Handles password hashing and JWT token lifecycle.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError

# ---------------------------------------------------------------------------
# Password hashing — bcrypt directly (passlib has bcrypt 4.x+ incompatibility)
# ---------------------------------------------------------------------------


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    Args:
        plain_password: The raw password from user input.

    Returns:
        A bcrypt hash string suitable for database storage.
    """
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored bcrypt hash.

    Args:
        plain_password: The raw password from user input.
        hashed_password: The stored bcrypt hash.

    Returns:
        True if the password matches, False otherwise.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------

_ACCESS_TOKEN_TYPE = "access"
_REFRESH_TOKEN_TYPE = "refresh"


def _create_token(
    data: dict[str, Any],
    token_type: str,
    expires_delta: timedelta,
) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    payload.update({"exp": expire, "type": token_type})
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(subject: str) -> str:
    """Create a short-lived JWT access token for the given subject (user UUID)."""
    return _create_token(
        data={"sub": subject},
        token_type=_ACCESS_TOKEN_TYPE,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(subject: str) -> str:
    """Create a long-lived JWT refresh token for the given subject (user UUID)."""
    return _create_token(
        data={"sub": subject},
        token_type=_REFRESH_TOKEN_TYPE,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_access_token(token: str) -> str:
    """
    Decode and validate a JWT access token, returning the subject (user UUID string).

    Raises:
        UnauthorizedError: If invalid, expired, or wrong type.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != _ACCESS_TOKEN_TYPE:
            raise UnauthorizedError("Invalid token type")
        subject: str | None = payload.get("sub")
        if subject is None:
            raise UnauthorizedError("Token missing subject claim")
        return subject
    except JWTError as exc:
        raise UnauthorizedError("Could not validate credentials") from exc


def decode_refresh_token(token: str) -> str:
    """
    Decode and validate a JWT refresh token, returning the subject (user UUID string).

    Raises:
        UnauthorizedError: If invalid, expired, or wrong type.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != _REFRESH_TOKEN_TYPE:
            raise UnauthorizedError("Invalid token type")
        subject: str | None = payload.get("sub")
        if subject is None:
            raise UnauthorizedError("Token missing subject claim")
        return subject
    except JWTError as exc:
        raise UnauthorizedError("Could not validate credentials") from exc
