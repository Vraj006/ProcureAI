from pydantic import BaseModel
from typing import Optional, Literal

class HumanReviewSubmit(BaseModel):
    status: Literal["approved", "rejected", "pending_review", "requires_changes"]
    comments: Optional[str] = None
