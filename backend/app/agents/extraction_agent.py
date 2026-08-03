"""
Extraction Agent.

Orchestrates the full procurement data extraction pipeline:

  raw_text  →  build_prompt  →  LLMService  →  parse JSON  →  validate Pydantic
               ↓                                              ↓
               extraction_prompt.py                 ProcurementExtractionResult
                                                             ↓
                                                   ExtractionAgentResult
"""

import json
from typing import Any

from app.core.logging import get_logger
from app.prompts.extraction_prompt import EXTRACTION_SYSTEM_PROMPT, build_user_prompt
from app.schemas.extraction_schema import (
    ExtractionAgentResult,
    ProcurementExtractionResult,
)
from app.services.llm_service import LLMService

logger = get_logger(__name__)


class ExtractionAgent:
    """
    Converts raw procurement document text into a validated structured result.

    All error conditions are caught and returned as a structured
    ``ExtractionAgentResult(success=False, errors=[...])`` — no raw
    exceptions are propagated to callers.
    """

    def __init__(self, llm_service: LLMService | None = None) -> None:
        """
        Args:
            llm_service: Optionally inject a custom LLMService (useful for testing).
                         If None, a default instance is constructed (reads MISTRAL_API_KEY).
        """
        self._llm = llm_service if llm_service is not None else LLMService()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def extract(self, raw_text: str) -> ExtractionAgentResult:
        """
        Extract structured procurement data from raw document text.

        Args:
            raw_text: Plain text extracted from a procurement PDF.

        Returns:
            ``ExtractionAgentResult`` — always has the same structure
            regardless of success or failure.
        """
        logger.info("ExtractionAgent.extract() — text length: %d chars", len(raw_text))

        # ── Guard: empty input ──────────────────────────────────────────
        if not raw_text or not raw_text.strip():
            logger.warning("Extraction skipped: empty raw_text supplied.")
            return ExtractionAgentResult(
                success=False,
                errors=["Input text is empty. Nothing to extract."],
            )

        # ── Step 1: Build prompt ────────────────────────────────────────
        user_prompt = build_user_prompt(raw_text)

        # ── Step 2: Call LLM ────────────────────────────────────────────
        try:
            raw_response = self._llm.complete_json(EXTRACTION_SYSTEM_PROMPT, user_prompt)
            logger.debug("Raw LLM response (first 500 chars): %.500s", raw_response)
        except Exception as exc:
            logger.error("LLM call failed: %s", exc)
            return ExtractionAgentResult(
                success=False,
                errors=[f"LLM service error: {exc}"],
            )

        # ── Step 3: Parse JSON ──────────────────────────────────────────
        try:
            parsed: dict[str, Any] = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            logger.error("LLM returned non-JSON response: %s", exc)
            return ExtractionAgentResult(
                success=False,
                errors=[f"LLM returned invalid JSON: {exc}"],
                raw_llm_response=raw_response,
            )

        # ── Step 4: Validate with Pydantic ──────────────────────────────
        try:
            result = ProcurementExtractionResult.model_validate(parsed)
        except Exception as exc:
            logger.error("Pydantic validation failed: %s", exc)
            return ExtractionAgentResult(
                success=False,
                errors=[f"Schema validation error: {exc}"],
                raw_llm_response=raw_response,
            )

        logger.info(
            "Extraction succeeded — vendor=%s  quotation=%s  items=%d",
            result.vendor.name if result.vendor else None,
            result.quotation.quotation_number if result.quotation else None,
            len(result.items),
        )

        return ExtractionAgentResult(
            success=True,
            data=result,
            raw_llm_response=raw_response,
        )
