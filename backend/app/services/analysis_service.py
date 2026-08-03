import uuid
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.exceptions import NotFoundError
from app.graph.workflow import run_procurement_workflow
from app.repositories.extracted_quotation_repository import ExtractedQuotationRepository
from app.repositories.project_repository import ProjectRepository
from app.services.llm_service import LLMService

from app.agents.comparison_agent import ComparisonAgent
from app.agents.compliance_agent import ComplianceAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.human_review.service import HumanReviewService
from app.human_review.schemas import HumanFeedback, ReviewStatus
from app.schemas.review import HumanReviewSubmit


class AnalysisService:
    def __init__(self, db: Session, llm_service: LLMService):
        self._db = db
        self._llm = llm_service
        self._project_repo = ProjectRepository(db)
        self._extraction_repo = ExtractedQuotationRepository(db)
        self._human_review_service = HumanReviewService()

    def _validate_project(self, workspace_id: uuid.UUID, project_id: uuid.UUID):
        project = self._project_repo.get_by_id(project_id)
        if not project or project.workspace_id != workspace_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found in this workspace")
        return project

    def start_analysis(self, workspace_id: uuid.UUID, project_id: uuid.UUID) -> Dict[str, Any]:
        self._validate_project(workspace_id, project_id)
        
        from app.models.quotation import QuotationStatus
        from app.repositories.quotation_repository import QuotationRepository
        from app.services.storage_service import get_storage_service
        from app.services.document_processor import DocumentProcessor
        from app.agents.extraction_agent import ExtractionAgent
        from app.services.extraction_persistence_service import ExtractionPersistenceService
        from fastapi import HTTPException, status
        
        quotation_repo = QuotationRepository(self._db)
        items, _ = quotation_repo.list_by_project(project_id, page_size=100)
        
        uploaded_quotations = [q for q in items if q.status == QuotationStatus.UPLOADED]
        if not uploaded_quotations:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No quotations uploaded yet")
            
        extractions = self._extraction_repo.get_by_project_id(project_id)
        extracted_q_ids = {e.quotation_id for e in extractions}
        
        storage = get_storage_service()
        doc_processor = DocumentProcessor()
        extraction_agent = ExtractionAgent(llm_service=self._llm)
        extraction_persistence = ExtractionPersistenceService(self._db)
        
        for q in uploaded_quotations:
            if q.id in extracted_q_ids:
                continue
            
            abs_path = storage.get_absolute_path(q.file_path)
            doc_result = doc_processor.process_document(abs_path)
            
            if not doc_result.success:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Failed to process document {q.file_name}: {doc_result.errors}")
                
            ext_result = extraction_agent.extract(doc_result.content.raw_text)
            if not ext_result.success:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Failed to extract text {q.file_name}: {ext_result.errors}")
                
            extraction_persistence.save_extraction(q.id, ext_result.data)

        # Fire off LangGraph
        try:
            state = run_procurement_workflow(project_id, self._db, self._llm)
            
            project = self._validate_project(workspace_id, project_id)
            meta = dict(project.metadata_) if project.metadata_ else {}
            if state.get("comparison_result"):
                meta["comparison"] = state["comparison_result"].model_dump(mode='json')
            if state.get("compliance_result"):
                meta["compliance"] = state["compliance_result"].model_dump(mode='json')
            if state.get("recommendation_result"):
                meta["recommendation"] = state["recommendation_result"].model_dump(mode='json')
                
            project.metadata_ = meta
            self._project_repo.update(project)
            self._db.commit()
            
        except Exception as e:
            self._db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Workflow failed: {str(e)}")

        return {
            "success": True,
            "message": "Analysis completed successfully.",
            "project_id": str(project_id),
            "workflow_status": "completed"
        }

    def get_workflow_status(self, workspace_id: uuid.UUID, project_id: uuid.UUID) -> Dict[str, Any]:
        project = self._validate_project(workspace_id, project_id)
        
        extractions = self._extraction_repo.get_by_project_id(project_id)
        has_extractions = len(extractions) > 0
        
        meta = project.metadata_ or {}
        has_comparison = "comparison" in meta
        has_compliance = "compliance" in meta
        has_recommendation = "recommendation" in meta
        
        # If the project cache is completely cleared by a new upload, we treat AI processing as pending.
        project_status = "completed" if has_recommendation else "pending"
        
        status_payload = {
            "project_id": str(project_id),
            "status": project_status,
            "steps": {
                "document_processing": "completed" if has_extractions else "pending",
                "extraction": "completed" if has_extractions else "pending",
                "comparison": "completed" if has_comparison else "pending",
                "compliance": "completed" if has_compliance else "pending",
                "recommendation": "completed" if has_recommendation else "pending",
                "human_review": "pending"  # Overridable
            }
        }
        
        if project.metadata_ and "human_review" in project.metadata_:
            status_payload["steps"]["human_review"] = project.metadata_["human_review"]

        return status_payload

    def get_extraction(self, workspace_id: uuid.UUID, project_id: uuid.UUID):
        self._validate_project(workspace_id, project_id)
        return self._extraction_repo.get_by_project_id(project_id)

    def get_comparison(self, workspace_id: uuid.UUID, project_id: uuid.UUID):
        project = self._validate_project(workspace_id, project_id)
        from app.schemas.comparison_schema import ComparisonAgentResult, ComparisonResult
        
        if not project.metadata_ or "comparison" not in project.metadata_:
            return ComparisonAgentResult(success=False, project_id=project_id, errors=["Analysis not complete. Waiting on Comparison module."])
            
        data = ComparisonResult.model_validate(project.metadata_["comparison"])
        return ComparisonAgentResult(success=True, project_id=project_id, data=data)

    def get_compliance(self, workspace_id: uuid.UUID, project_id: uuid.UUID):
        project = self._validate_project(workspace_id, project_id)
        from app.schemas.compliance_schema import ComplianceAgentResult, ComplianceResult
        
        if not project.metadata_ or "compliance" not in project.metadata_:
             return ComplianceAgentResult(success=False, project_id=project_id, errors=["Analysis not complete. Waiting on Compliance module."])
             
        data = ComplianceResult.model_validate(project.metadata_["compliance"])
        return ComplianceAgentResult(success=True, project_id=project_id, data=data)

    def get_recommendation(self, workspace_id: uuid.UUID, project_id: uuid.UUID):
        project = self._validate_project(workspace_id, project_id)
        from app.schemas.recommendation_schema import RecommendationAgentResult, RecommendationResult
        
        if not project.metadata_ or "recommendation" not in project.metadata_:
            return RecommendationAgentResult(success=False, project_id=project_id, errors=["Analysis not complete. Waiting on Recommendation module."])
            
        data = RecommendationResult.model_validate(project.metadata_["recommendation"])
        return RecommendationAgentResult(success=True, project_id=project_id, data=data)

    def submit_human_review(self, workspace_id: uuid.UUID, project_id: uuid.UUID, payload: HumanReviewSubmit):
        self._validate_project(workspace_id, project_id)
        
        status_map = {
            "approved": ReviewStatus.APPROVED,
            "rejected": ReviewStatus.REJECTED,
            "pending_review": ReviewStatus.PENDING_REVIEW,
            "requires_changes": ReviewStatus.REQUIRES_CHANGES
        }
        mapped_status = status_map.get(payload.status, ReviewStatus.PENDING_REVIEW)
        
        feedback = HumanFeedback(
            project_id=project_id,
            status=mapped_status,
            reviewer_comments=payload.comments,
            rejection_reason=payload.comments if mapped_status == ReviewStatus.REJECTED else None
        )
        
        try:
            # Invoking LangGraph natively correctly patches recommendations under the hood! 
            state = run_procurement_workflow(project_id, self._db, self._llm, human_feedback=feedback)
            
            project = self._validate_project(workspace_id, project_id)
            if state.get("recommendation_result"):
                meta = dict(project.metadata_) if project.metadata_ else {}
                meta["recommendation"] = state["recommendation_result"].model_dump(mode='json')
                meta["human_review"] = payload.status
                project.metadata_ = meta
                self._project_repo.update(project)
                self._db.commit()
                
        except Exception as e:
            self._db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to submit review orchestration: {str(e)}")
            
        return {"success": True, "message": "Review submitted successfully."}
