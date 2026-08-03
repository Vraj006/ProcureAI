"""
Global exception handler middleware.

Maps ProcureAI domain exceptions to consistent JSON HTTP responses.
Register via add_exception_handlers(app) in main.py.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    InactiveAccountError,
    NotFoundError,
    ProcureAIException,
    UnauthorizedError,
    ValidationError,
)


def _error_response(status_code: int, message: str, error_code: str) -> JSONResponse:
    """Build a consistent error JSON response."""
    return JSONResponse(
        status_code=status_code,
        content={"detail": message, "error_code": error_code},
    )


def add_exception_handlers(app: FastAPI) -> None:
    """
    Register all ProcureAI domain exception handlers on the given FastAPI app.

    Call this inside create_app() after middleware registration.
    """

    @app.exception_handler(NotFoundError)
    async def _not_found(_req: Request, exc: NotFoundError) -> JSONResponse:
        return _error_response(404, exc.message, exc.error_code)

    @app.exception_handler(UnauthorizedError)
    async def _unauthorized(_req: Request, exc: UnauthorizedError) -> JSONResponse:
        return _error_response(401, exc.message, exc.error_code)

    @app.exception_handler(InactiveAccountError)
    async def _inactive(_req: Request, exc: InactiveAccountError) -> JSONResponse:
        return _error_response(403, exc.message, exc.error_code)

    @app.exception_handler(ForbiddenError)
    async def _forbidden(_req: Request, exc: ForbiddenError) -> JSONResponse:
        return _error_response(403, exc.message, exc.error_code)

    @app.exception_handler(ConflictError)
    async def _conflict(_req: Request, exc: ConflictError) -> JSONResponse:
        return _error_response(409, exc.message, exc.error_code)

    @app.exception_handler(ValidationError)
    async def _validation(_req: Request, exc: ValidationError) -> JSONResponse:
        return _error_response(422, exc.message, exc.error_code)

    @app.exception_handler(ProcureAIException)
    async def _generic(_req: Request, exc: ProcureAIException) -> JSONResponse:
        return _error_response(500, exc.message, exc.error_code)
