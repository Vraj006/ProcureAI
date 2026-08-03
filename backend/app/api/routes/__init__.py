"""
API route modules package.

Organizes endpoints by domain (health, projects, quotations, etc.).
Each module defines an APIRouter that is included in the main application.
"""

from app.api.routes.health import router as health_router

__all__ = ["health_router"]
