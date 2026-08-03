"""
Health check response schema.

Defines the structure of the root health endpoint response
for OpenAPI documentation and client validation.
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response model for the service health check endpoint."""

    status: str = Field(
        ...,
        description="Current operational status of the service",
        examples=["running"],
    )
    service: str = Field(
        ...,
        description="Human-readable service name",
        examples=["ProcureAI Backend"],
    )
