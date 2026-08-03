"""
Health endpoint tests.

Verifies the root health check endpoint returns the expected
response structure and status code.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_check_returns_running_status() -> None:
    """GET / should return status running and service name."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["service"] == "ProcureAI Backend"


def test_openapi_docs_available() -> None:
    """OpenAPI documentation should be accessible at /docs."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema_available() -> None:
    """OpenAPI JSON schema should be accessible at /openapi.json."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "ProcureAI Backend"
