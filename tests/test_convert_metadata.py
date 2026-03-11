"""
Offline tests for the convert metadata stage — no real LLM calls.

Run with:
    poetry run pytest tests/test_convert_metadata.py -v
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from src.convert.metadata import (
    _parse_json_response,
    extract_metadata,
    metadata_to_yaml_frontmatter,
)
from src.convert.profiles import get_profile


@pytest.fixture()
def profile():
    return get_profile("financial_rfp")


# ---------------------------------------------------------------------------
# _parse_json_response
# ---------------------------------------------------------------------------

def test_parse_valid_json(profile):
    raw = json.dumps({"issuer": "Acme Corp", "title": "RFP 2025"})
    result = _parse_json_response(raw, profile.metadata_schema)
    assert result["issuer"] == "Acme Corp"
    assert result["title"] == "RFP 2025"
    # Missing keys should be None
    assert result["deadline"] is None


def test_parse_json_with_code_fence(profile):
    raw = '```json\n{"issuer": "Acme Corp"}\n```'
    result = _parse_json_response(raw, profile.metadata_schema)
    assert result["issuer"] == "Acme Corp"


def test_parse_invalid_json_returns_nulls(profile):
    raw = "This is not JSON at all."
    result = _parse_json_response(raw, profile.metadata_schema)
    assert all(v is None for v in result.values())
    assert set(result.keys()) == set(profile.metadata_schema.keys())


def test_parse_ignores_extra_keys(profile):
    raw = json.dumps({"issuer": "Acme", "unknown_field": "surprise"})
    result = _parse_json_response(raw, profile.metadata_schema)
    assert "unknown_field" not in result
    assert result["issuer"] == "Acme"


# ---------------------------------------------------------------------------
# metadata_to_yaml_frontmatter
# ---------------------------------------------------------------------------

def test_yaml_frontmatter_basic():
    meta = {"title": "Test RFP", "issuer": None, "deadline": "2025-06-01"}
    fm = metadata_to_yaml_frontmatter(meta)
    assert fm.startswith("---")
    assert fm.endswith("---")
    assert "title: Test RFP" in fm
    assert "issuer: null" in fm
    assert "deadline: 2025-06-01" in fm


def test_yaml_frontmatter_quotes_special_chars():
    meta = {"title": "RFP: Phase 1"}
    fm = metadata_to_yaml_frontmatter(meta)
    assert '"RFP: Phase 1"' in fm


def test_yaml_frontmatter_empty():
    assert metadata_to_yaml_frontmatter({}) == ""


# ---------------------------------------------------------------------------
# extract_metadata (mocked OpenAI)
# ---------------------------------------------------------------------------

def test_extract_metadata_calls_openai(profile):
    fake_response = MagicMock()
    fake_response.choices = [
        MagicMock(message=MagicMock(content=json.dumps({
            "issuer": "Test Bank",
            "title": "Investment RFP",
            "reference": "RFP-001",
            "issue_date": "2025-01-15",
            "deadline": "2025-03-01",
            "contact_name": "Jane Doe",
            "contact_email": "jane@test.com",
            "scope_summary": "Portfolio management services",
            "value": "$5M",
        })))
    ]

    with patch("src.convert.metadata.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = fake_response

        result = extract_metadata("Some markdown content", profile, "fake-key")

    assert result["issuer"] == "Test Bank"
    assert result["deadline"] == "2025-03-01"
    mock_client.chat.completions.create.assert_called_once()


def test_extract_metadata_no_schema():
    """Profile with no metadata_schema should return empty dict."""
    from src.convert.profiles.base import ConversionProfile
    empty_profile = ConversionProfile(name="empty", llamaparse_instructions="")
    result = extract_metadata("text", empty_profile, "key")
    assert result == {}
