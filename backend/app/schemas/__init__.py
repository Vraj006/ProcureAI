"""
Pydantic schema models package.

Defines request and response data transfer objects (DTOs) used by API
endpoints. Schemas enforce validation, serialization, and OpenAPI docs.
"""

from app.schemas.health import HealthResponse

__all__ = ["HealthResponse"]
