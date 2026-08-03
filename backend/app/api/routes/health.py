"""
Health check endpoint module.

Provides a root endpoint for service availability monitoring
and load balancer health probes.
"""

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Service health check",
    description="Returns the current operational status of the ProcureAI backend.",
)
async def health_check() -> HealthResponse:
    """
    Root health check endpoint.

    Used by orchestrators, load balancers, and monitoring systems
    to verify the service is running and accepting requests.
    """
    return HealthResponse(
        status="running",
        service=settings.app_name,
    )
