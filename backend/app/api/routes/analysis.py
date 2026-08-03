import uuid
from typing import Dict, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.llm_service import LLMService
from app.api.dependencies.auth import get_current_active_user
from app.schemas.analysis import StartAnalysisResponse
from app.schemas.workflow import WorkflowStatusResponse
from app.schemas.review import HumanReviewSubmit
from app.services.analysis_service import AnalysisService
from app.services.llm_service import LLMService
from app.models.user import User

router = APIRouter(
    prefix="/workspaces/{workspace_id}/projects/{project_id}",
    tags=["Analysis"],
)


def get_analysis_service(
    db: Session = Depends(get_db)
) -> AnalysisService:
    # LLMService instantiated natively as it requires no connection pooling
    return AnalysisService(db=db, llm_service=LLMService())


@router.post(
    "/analyze",
    response_model=StartAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Start procurement analysis",
)
def start_analysis(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    current_user: User = Depends(get_current_active_user),
):
    """Start the complete LangGraph procurement workflow."""
    return analysis_service.start_analysis(workspace_id, project_id)


@router.get(
    "/workflow",
    response_model=WorkflowStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get workflow progress",
)
def get_workflow_status(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve the progress and status of the current workflow steps."""
    return analysis_service.get_workflow_status(workspace_id, project_id)


@router.get(
    "/extraction",
    status_code=status.HTTP_200_OK,
    summary="Return previously stored extracted quotation data",
)
def get_extraction(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    current_user: User = Depends(get_current_active_user),
):
    return analysis_service.get_extraction(workspace_id, project_id)


@router.get(
    "/comparison",
    status_code=status.HTTP_200_OK,
    summary="Retrieve Comparison engine results securely",
)
def get_comparison(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    current_user: User = Depends(get_current_active_user),
):
    return analysis_service.get_comparison(workspace_id, project_id)


@router.get(
    "/compliance",
    status_code=status.HTTP_200_OK,
    summary="Retrieve Compliance validation results safely",
)
def get_compliance(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    current_user: User = Depends(get_current_active_user),
):
    return analysis_service.get_compliance(workspace_id, project_id)


@router.get(
    "/recommendation",
    status_code=status.HTTP_200_OK,
    summary="Retrieve final mathematical AI recommendations",
)
def get_recommendation(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    current_user: User = Depends(get_current_active_user),
):
    return analysis_service.get_recommendation(workspace_id, project_id)


@router.post(
    "/review",
    status_code=status.HTTP_200_OK,
    summary="Submit Human Review overriding recommendations",
)
def submit_review(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: HumanReviewSubmit,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    current_user: User = Depends(get_current_active_user),
):
    return analysis_service.submit_human_review(workspace_id, project_id, payload)
