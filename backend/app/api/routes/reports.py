import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.report_service import ReportService

router = APIRouter(
    prefix="/workspaces",
    tags=["Reports"],
)

@router.get("/{workspace_id}/projects/{project_id}/report/pdf", summary="Download Executive PDF")
def download_executive_pdf(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    report_service = ReportService(db)
    pdf_buffer = report_service.generate_pdf_report(workspace_id, project_id)
    
    headers = {
        'Content-Disposition': f'attachment; filename="procureai_executive_report_{project_id}.pdf"'
    }
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers=headers
    )


@router.get("/{workspace_id}/projects/{project_id}/report/excel", summary="Download Executive Excel")
def download_executive_excel(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    report_service = ReportService(db)
    excel_buffer = report_service.generate_excel_report(workspace_id, project_id)
    
    headers = {
        'Content-Disposition': f'attachment; filename="procureai_executive_report_{project_id}.xlsx"'
    }
    
    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )
