"""
Unit tests for ExtractionAgent.

All tests mock LLMService.complete_json() so they run without
a real Mistral API key and without network access.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.agents.extraction_agent import ExtractionAgent
from app.services.llm_service import LLMService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_LLM_RESPONSE = json.dumps({
    "vendor": {
        "name": "Acme Supplies Ltd.",
        "address": "42 Industrial Park, Mumbai - 400001",
        "email": "sales@acme.com",
        "phone": "+91-22-12345678",
        "gst_number": "27ABCDE1234F1Z5",
    },
    "quotation": {
        "quotation_number": "Q-2024-0987",
        "quotation_date": "2024-07-15",
        "currency": "INR",
        "valid_until": "2024-08-15",
    },
    "items": [
        {
            "item_name": "Industrial Pump",
            "description": "High-pressure centrifugal pump, 50HP",
            "quantity": 5.0,
            "unit": "units",
            "unit_price": 85000.0,
            "total_price": 425000.0,
        }
    ],
    "pricing": {
        "subtotal": 425000.0,
        "discount": 12750.0,
        "shipping_cost": 5000.0,
        "tax": 74025.0,
        "grand_total": 491275.0,
    },
    "commercial_terms": {
        "payment_terms": "30% advance, 70% on delivery",
        "delivery_time": "6-8 weeks",
        "warranty": "12 months on-site warranty",
        "incoterms": "DAP Mumbai",
    },
})

PARTIAL_LLM_RESPONSE = json.dumps({
    "vendor": {"name": "Generic Vendor"},
    "quotation": None,
    "items": [],
    "pricing": None,
    "commercial_terms": None,
})


def make_agent(llm_response: str) -> ExtractionAgent:
    """Create an ExtractionAgent with a mocked LLMService."""
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.complete_json.return_value = llm_response
    return ExtractionAgent(llm_service=mock_llm)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestExtractionAgentSuccess:
    def test_full_extraction_returns_success(self):
        agent = make_agent(VALID_LLM_RESPONSE)
        result = agent.extract("Some raw procurement text about industrial pumps.")

        assert result.success is True
        assert result.data is not None
        assert result.errors == []

    def test_vendor_fields_are_populated(self):
        agent = make_agent(VALID_LLM_RESPONSE)
        result = agent.extract("raw text")

        vendor = result.data.vendor
        assert vendor is not None
        assert vendor.name == "Acme Supplies Ltd."
        assert vendor.email == "sales@acme.com"
        assert vendor.gst_number == "27ABCDE1234F1Z5"

    def test_quotation_fields_are_populated(self):
        agent = make_agent(VALID_LLM_RESPONSE)
        result = agent.extract("raw text")

        q = result.data.quotation
        assert q is not None
        assert q.quotation_number == "Q-2024-0987"
        assert q.currency == "INR"

    def test_items_list_is_populated(self):
        agent = make_agent(VALID_LLM_RESPONSE)
        result = agent.extract("raw text")

        items = result.data.items
        assert len(items) == 1
        assert items[0].item_name == "Industrial Pump"
        assert items[0].quantity == 5.0
        assert items[0].total_price == 425000.0

    def test_pricing_is_populated(self):
        agent = make_agent(VALID_LLM_RESPONSE)
        result = agent.extract("raw text")

        pricing = result.data.pricing
        assert pricing is not None
        assert pricing.grand_total == 491275.0

    def test_commercial_terms_are_populated(self):
        agent = make_agent(VALID_LLM_RESPONSE)
        result = agent.extract("raw text")

        ct = result.data.commercial_terms
        assert ct is not None
        assert ct.payment_terms == "30% advance, 70% on delivery"
        assert ct.warranty == "12 months on-site warranty"

    def test_raw_llm_response_is_preserved(self):
        agent = make_agent(VALID_LLM_RESPONSE)
        result = agent.extract("raw text")

        assert result.raw_llm_response is not None
        assert "Acme Supplies" in result.raw_llm_response


class TestExtractionAgentPartialData:
    def test_null_fields_accepted(self):
        """Null quotation, pricing, and items should not cause failure."""
        agent = make_agent(PARTIAL_LLM_RESPONSE)
        result = agent.extract("sparse document text")

        assert result.success is True
        assert result.data.vendor.name == "Generic Vendor"
        assert result.data.quotation is None
        assert result.data.items == []
        assert result.data.pricing is None


class TestExtractionAgentEmptyInput:
    def test_empty_string_returns_error(self):
        agent = make_agent("{}")
        result = agent.extract("")

        assert result.success is False
        assert any("empty" in e.lower() for e in result.errors)
        assert result.data is None

    def test_whitespace_only_returns_error(self):
        agent = make_agent("{}")
        result = agent.extract("   \n\t  ")

        assert result.success is False
        assert result.data is None


class TestExtractionAgentLLMFailure:
    def test_invalid_json_from_llm(self):
        agent = make_agent("This is not JSON at all!!!")
        result = agent.extract("some document text")

        assert result.success is False
        assert any("json" in e.lower() for e in result.errors)
        assert result.raw_llm_response == "This is not JSON at all!!!"

    def test_json_with_markdown_fences_is_stripped(self):
        """Fenced JSON should still parse correctly (stripping happens in LLMService)."""
        # Simulate LLMService already returning stripped JSON
        agent = make_agent(PARTIAL_LLM_RESPONSE)
        result = agent.extract("document text")
        assert result.success is True

    def test_llm_api_error_returns_structured_failure(self):
        mock_llm = MagicMock(spec=LLMService)
        mock_llm.complete_json.side_effect = RuntimeError("API timeout")
        agent = ExtractionAgent(llm_service=mock_llm)

        result = agent.extract("some document text")

        assert result.success is False
        assert any("LLM service error" in e for e in result.errors)
        assert result.data is None


class TestMarkdownFenceStripping:
    """Test the fence-stripping utility in isolation."""

    def test_strips_code_fence(self):
        from app.services.llm_service import _strip_fences

        fenced = "```json\n{\"key\": \"value\"}\n```"
        assert _strip_fences(fenced) == '{"key": "value"}'

    def test_strips_plain_fence(self):
        from app.services.llm_service import _strip_fences

        fenced = "```\n{\"key\": \"value\"}\n```"
        assert _strip_fences(fenced) == '{"key": "value"}'

    def test_no_fence_unchanged(self):
        from app.services.llm_service import _strip_fences

        clean = '{"key": "value"}'
        assert _strip_fences(clean) == clean
