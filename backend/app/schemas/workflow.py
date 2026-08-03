from pydantic import BaseModel
from typing import Dict, Any

class WorkflowStatusResponse(BaseModel):
    project_id: str
    status: str
    steps: Dict[str, str]
