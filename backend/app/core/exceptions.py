"""
Custom exception hierarchy for ProcureAI.

All domain exceptions inherit from ProcureAIException.
The global error handler in middleware maps each exception to
the correct HTTP status code and consistent JSON error response.
"""


class ProcureAIException(Exception):
    """
    Base exception for all ProcureAI domain errors.

    Attributes:
        message: Human-readable error description.
        error_code: Machine-readable error code for client consumers.
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        error_code: str = "INTERNAL_ERROR",
    ) -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class NotFoundError(ProcureAIException):
    """Raised when a requested resource does not exist or has been soft-deleted."""

    def __init__(
        self,
        message: str = "Resource not found",
        error_code: str = "NOT_FOUND",
    ) -> None:
        super().__init__(message=message, error_code=error_code)


class UnauthorizedError(ProcureAIException):
    """Raised when authentication credentials are missing or invalid."""

    def __init__(
        self,
        message: str = "Authentication required",
        error_code: str = "UNAUTHORIZED",
    ) -> None:
        super().__init__(message=message, error_code=error_code)


class ForbiddenError(ProcureAIException):
    """Raised when an authenticated user lacks permission for the operation."""

    def __init__(
        self,
        message: str = "Access denied",
        error_code: str = "FORBIDDEN",
    ) -> None:
        super().__init__(message=message, error_code=error_code)


class ConflictError(ProcureAIException):
    """Raised when an operation violates a uniqueness constraint (e.g. duplicate email)."""

    def __init__(
        self,
        message: str = "Resource already exists",
        error_code: str = "CONFLICT",
    ) -> None:
        super().__init__(message=message, error_code=error_code)


class ValidationError(ProcureAIException):
    """Raised when business-level validation fails (distinct from Pydantic schema validation)."""

    def __init__(
        self,
        message: str = "Validation failed",
        error_code: str = "VALIDATION_ERROR",
    ) -> None:
        super().__init__(message=message, error_code=error_code)


class InactiveAccountError(ProcureAIException):
    """Raised when a deactivated user attempts to authenticate."""

    def __init__(
        self,
        message: str = "Account is inactive",
        error_code: str = "INACTIVE_ACCOUNT",
    ) -> None:
        super().__init__(message=message, error_code=error_code)
