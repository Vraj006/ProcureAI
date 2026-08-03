"""
Core infrastructure module.

Contains cross-cutting concerns such as application configuration,
logging setup, and shared constants used across the entire application.
"""

from app.core.config import settings

__all__ = ["settings"]
