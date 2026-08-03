"""
API layer package.

Contains HTTP route definitions, request/response handling, and API
versioning. Routes delegate business logic to the services layer.
"""

from app.api.routes import health_router

__all__ = ["health_router"]
