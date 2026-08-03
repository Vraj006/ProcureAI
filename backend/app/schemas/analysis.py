from pydantic import BaseModel
from typing import Optional

class StartAnalysisResponse(BaseModel):
    success: bool
    message: str
    project_id: str
    workflow_status: str
