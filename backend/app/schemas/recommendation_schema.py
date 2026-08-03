"""
Pydantic schemas for Recommendation Agent output.
"""

from typing import Optional

from pydantic import BaseModel, Field


class RecommendationResult(BaseModel):
    """
    Structured output of the Recommendation Agent.

    ``recommended_vendor`` is None when no eligible vendor exists.
    ``confidence_score`` is 0–100, computed deterministically from
    price rank, compliance status, and metric wins.
    ``reasoning``, ``strengths``, ``risks``, and ``alternatives`` are
    LLM-generated; they are None / empty when the LLM is unavailable.
    ``is_deterministic_fallback`` is True when the LLM call failed
    and the agent fell back to deterministic-only output.
    ``is_no_recommendation`` is True when no compliant vendor exists.
    """

    recommended_vendor: Optional[str] = None
    confidence_score: int = 0
    reasoning: Optional[str] = None
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    is_no_recommendation: bool = False
    is_deterministic_fallback: bool = False


class RecommendationAgentResult(BaseModel):
    """Wrapper returned by RecommendationAgent.recommend()."""

    success: bool
    data: Optional[RecommendationResult] = None
    errors: list[str] = Field(default_factory=list)
