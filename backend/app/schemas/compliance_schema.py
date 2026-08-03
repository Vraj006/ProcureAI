"""
Pydantic schemas for structured compliance evaluation results.
"""

import enum
import uuid
from typing import Optional

from pydantic import BaseModel, Field


class Severity(str, enum.Enum):
    """Severity of a compliance issue."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ComplianceStatus(str, enum.Enum):
    """Overall compliance status of a single quotation."""

    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"


class ComplianceIssue(BaseModel):
    """A single failed or warned compliance check."""

    check_name: str
    severity: Severity
    message: str


class QuotationCompliance(BaseModel):
    """
    Compliance evaluation result for one ExtractedQuotation.

    ``passed_checks`` counts all checks that produced no issue.
    ``failed_checks`` counts ERROR-severity issues only.
    ``warning_count`` counts WARNING-severity issues only.
    """

    quotation_id: uuid.UUID
    vendor_name: Optional[str] = None
    status: ComplianceStatus
    passed_checks: int
    failed_checks: int
    warning_count: int
    issues: list[ComplianceIssue] = Field(default_factory=list)


class ComplianceResult(BaseModel):
    """
    Aggregated compliance report across all quotations in a project.
    """

    project_id: uuid.UUID
    total_quotations: int
    compliant_count: int
    partially_compliant_count: int
    non_compliant_count: int
    quotation_results: list[QuotationCompliance] = Field(default_factory=list)
    summary: Optional[str] = None   # set by agent after optional LLM call


class ComplianceAgentResult(BaseModel):
    """
    Wrapper returned by ComplianceAgent.evaluate().

    Success can be True even with zero quotations — an empty project is
    not a failure, it simply yields a result with zero counts.
    """

    success: bool
    data: Optional[ComplianceResult] = None
    errors: list[str] = Field(default_factory=list)
