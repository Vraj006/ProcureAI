import uuid
import pytest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from main import app
from app.services.analysis_service import AnalysisService
from app.schemas.comparison_schema import ComparisonAgentResult
from app.schemas.compliance_schema import ComplianceAgentResult
from app.schemas.recommendation_schema import RecommendationAgentResult

client = TestClient(app)

WID = str(uuid.uuid4())
PID = str(uuid.uuid4())
BASE_URL = f"/api/v1/workspaces/{WID}/projects/{PID}"


@pytest.fixture(autouse=True)
def override_dependencies():
    from app.api.dependencies.auth import get_current_active_user
    from app.models.user import User
    from app.api.routes.analysis import get_analysis_service
    
    dummy_user = User(id=uuid.uuid4(), email="test@test.com")
    mock_service = MagicMock(spec=AnalysisService)
    
    app.dependency_overrides[get_current_active_user] = lambda: dummy_user
    app.dependency_overrides[get_analysis_service] = lambda: mock_service
    
    yield mock_service
    app.dependency_overrides.clear()


def test_analyze_endpoint(override_dependencies):
    mock_service = override_dependencies
    mock_service.start_analysis.return_value = {
        "success": True,
        "message": "Analysis completed successfully.",
        "project_id": PID,
        "workflow_status": "completed"
    }
    
    resp = client.post(f"{BASE_URL}/analyze")
    assert resp.status_code == 200
    assert resp.json()["workflow_status"] == "completed"
    mock_service.start_analysis.assert_called_once()


def test_workflow_status_endpoint(override_dependencies):
    mock_service = override_dependencies
    mock_service.get_workflow_status.return_value = {
        "project_id": PID,
        "status": "completed",
        "steps": {
            "document_processing": "completed",
            "extraction": "completed",
            "comparison": "completed",
            "compliance": "completed",
            "recommendation": "completed",
            "human_review": "pending"
        }
    }
    
    resp = client.get(f"{BASE_URL}/workflow")
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


def test_extraction_endpoint(override_dependencies):
    mock_service = override_dependencies
    mock_service.get_extraction.return_value = [{"id": str(uuid.uuid4()), "vendor_name": "Acme Corp"}]
    
    resp = client.get(f"{BASE_URL}/extraction")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_comparison_endpoint(override_dependencies):
    mock_service = override_dependencies
    mock_service.get_comparison.return_value = ComparisonAgentResult(
        success=True, project_id=uuid.UUID(PID)
    )
    
    resp = client.get(f"{BASE_URL}/comparison")
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_compliance_endpoint(override_dependencies):
    mock_service = override_dependencies
    mock_service.get_compliance.return_value = ComplianceAgentResult(
        success=True, project_id=uuid.UUID(PID)
    )
    
    resp = client.get(f"{BASE_URL}/compliance")
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_recommendation_endpoint(override_dependencies):
    mock_service = override_dependencies
    mock_service.get_recommendation.return_value = RecommendationAgentResult(
        success=True, project_id=uuid.UUID(PID)
    )
    
    resp = client.get(f"{BASE_URL}/recommendation")
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_submit_review_endpoint(override_dependencies):
    mock_service = override_dependencies
    mock_service.submit_human_review.return_value = {"success": True, "message": "Done."}
    
    payload = {"status": "approved", "comments": "Looks good."}
    resp = client.post(f"{BASE_URL}/review", json=payload)
    assert resp.status_code == 200
    assert resp.json()["success"] is True
