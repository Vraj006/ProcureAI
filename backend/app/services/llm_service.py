"""
LLM Service — Mistral API wrapper.

Generic communication layer with the Mistral API.
Contains NO procurement-specific logic.

Responsibilities:
- Manage the Mistral client lifecycle.
- Request JSON-mode completions.
- Strip markdown code fences from responses.
- Retry on transient failures with exponential back-off.
- Enforce a configurable request timeout.
"""

import json
import os
import re
import time

from app.core.logging import get_logger

logger = get_logger(__name__)

# Default model and behaviour constants
_DEFAULT_MODEL = "mistral-small-latest"
_DEFAULT_TIMEOUT = 60          # seconds
_DEFAULT_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.5        # seconds, doubles on each retry

# Transient HTTP status codes worth retrying
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_MARKDOWN_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?|\n?```\s*$", re.MULTILINE)


def _strip_fences(text: str) -> str:
    """Remove markdown ``` / ```json fences that an LLM may wrap JSON in."""
    return _MARKDOWN_FENCE_RE.sub("", text).strip()


from app.core.config import settings

class LLMService:
    """
    Wrapper around the Mistral Chat Completions API.

    Usage::

        svc = LLMService()
        json_str = svc.complete_json(system_prompt, user_content)
        data = json.loads(json_str)
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = _DEFAULT_MODEL,
        timeout: float = _DEFAULT_TIMEOUT,
        max_retries: int = _DEFAULT_MAX_RETRIES,
    ) -> None:
        resolved_key = api_key or settings.mistral_api_key or os.environ.get("MISTRAL_API_KEY")
        if not resolved_key:
            raise RuntimeError(
                "MISTRAL_API_KEY is not set. "
                "Add it to your .env file or environment variables."
            )

        try:
            from mistralai.client import Mistral
        except ImportError as exc:
            raise RuntimeError(
                "mistralai package is not installed or out of date. "
                "Run: pip install mistralai"
            ) from exc

        self._client = Mistral(api_key=resolved_key)
        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def complete_json(
        self,
        system_prompt: str,
        user_content: str,
        model: str | None = None,
    ) -> str:
        """
        Send a chat completion request and return the raw JSON string.

        Uses Mistral's ``response_format={"type": "json_object"}`` when
        available so that the API guarantees valid JSON output.

        Args:
            system_prompt: Instruction / task description for the model.
            user_content:  The actual content the model should analyse.
            model:         Override the default model for this call.

        Returns:
            Raw JSON string (markdown fences stripped).

        Raises:
            RuntimeError: After all retries are exhausted.
        """
        chosen_model = model or self._model
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content},
        ]

        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                logger.debug(
                    "LLM request attempt %d/%d  model=%s",
                    attempt, self._max_retries, chosen_model,
                )
                response = self._client.chat.complete(
                    model=chosen_model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.0,
                )
                raw = response.choices[0].message.content or ""
                return _strip_fences(raw)

            except Exception as exc:
                last_error = exc
                retryable = self._is_retryable(exc)
                logger.warning(
                    "LLM call failed (attempt %d/%d, retryable=%s): %s",
                    attempt, self._max_retries, retryable, exc,
                )
                if attempt < self._max_retries and retryable:
                    delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    logger.info("Retrying after %.1fs …", delay)
                    time.sleep(delay)
                else:
                    break

        raise RuntimeError(
            f"LLM request failed after {self._max_retries} attempt(s): {last_error}"
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        """
        Determine whether an exception is worth retrying.

        Handles MistralAPIStatusException (with status_code) and generic
        connection / timeout errors.
        """
        status = getattr(exc, "status_code", None)
        if status is not None:
            return int(status) in _RETRYABLE_STATUS

        name = type(exc).__name__.lower()
        return any(kw in name for kw in ("timeout", "connection", "network", "rate"))
