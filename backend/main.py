"""
ProcureAI Backend — Application Entry Point.

Creates and configures the FastAPI application instance with middleware,
lifecycle events, logging, and API route registration.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.workspaces import router as workspaces_router
from app.api.routes.projects import router as projects_router
from app.api.routes.vendors import router as vendors_router
from app.api.routes.quotations import router as quotations_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.reports import router as reports_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.database.database import check_database_connection
from app.middleware.error_handler import add_exception_handlers

logger = get_logger(__name__)

_API_V1_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown logic such as logging initialization,
    database connectivity checks, and resource cleanup.
    """
    # --- Startup ---
    setup_logging(debug=settings.debug)
    print("ProcureAI Backend Started")
    logger.info("ProcureAI Backend Started")
    logger.info("Service: %s v%s", settings.app_name, settings.app_version)
    logger.info("Debug mode: %s", settings.debug)

    check_database_connection()
    logger.info("All startup checks passed")

    yield

    # --- Shutdown ---
    print("ProcureAI Backend Shutdown")
    logger.info("ProcureAI Backend Shutdown")


def create_app() -> FastAPI:
    """
    Application factory.

    Builds and returns a fully configured FastAPI instance.
    Separating creation from module-level instantiation enables
    easier testing and multiple deployment configurations.
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Autonomous Procurement Intelligence Platform — "
            "AI-powered quotation analysis, vendor comparison, and compliance checking."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS — allow frontend on localhost:3000
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register domain exception handlers
    add_exception_handlers(app)

    # Health check (root)
    app.include_router(health_router)

    # API v1 routes
    app.include_router(auth_router, prefix=_API_V1_PREFIX)
    app.include_router(users_router, prefix=_API_V1_PREFIX)
    app.include_router(workspaces_router, prefix=_API_V1_PREFIX)
    app.include_router(projects_router, prefix=_API_V1_PREFIX)
    app.include_router(vendors_router, prefix=_API_V1_PREFIX)
    app.include_router(quotations_router, prefix=_API_V1_PREFIX)
    app.include_router(analysis_router, prefix=_API_V1_PREFIX)
    app.include_router(reports_router, prefix=_API_V1_PREFIX)

    return app


# Application instance used by ASGI servers (uvicorn, gunicorn)
app = create_app()
