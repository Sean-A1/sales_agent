"""
Tests for conversion profiles — no network / LLM calls.

Run with:
    poetry run pytest tests/test_convert_profiles.py -v
"""
from __future__ import annotations

import pytest

from src.convert.profiles import get_profile
from src.convert.profiles.base import ConversionProfile


class TestGetProfile:
    def test_financial_rfp(self):
        p = get_profile("financial_rfp")
        assert isinstance(p, ConversionProfile)
        assert p.name == "financial_rfp"

    def test_manufacturing(self):
        p = get_profile("manufacturing")
        assert isinstance(p, ConversionProfile)
        assert p.name == "manufacturing"

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown conversion profile"):
            get_profile("nonexistent")


class TestManufacturingProfile:
    @pytest.fixture()
    def profile(self):
        return get_profile("manufacturing")

    def test_premium_mode_enabled(self, profile):
        assert profile.premium_mode is True

    def test_convert_image_tags_enabled(self, profile):
        assert profile.convert_image_tags is True

    def test_llamaparse_system_prompt_nonempty(self, profile):
        assert profile.llamaparse_system_prompt != ""

    def test_metadata_schema_keys(self, profile):
        expected = {"device_name", "doc_title", "doc_type", "version", "date", "summary"}
        assert set(profile.metadata_schema.keys()) == expected

    def test_metadata_prompt_template_has_placeholders(self, profile):
        assert "{header}" in profile.metadata_prompt_template
        assert "{footer}" in profile.metadata_prompt_template
        assert "{schema_description}" in profile.metadata_prompt_template


class TestFinancialRfpProfile:
    def test_premium_mode_disabled(self):
        p = get_profile("financial_rfp")
        assert p.premium_mode is False

    def test_llamaparse_system_prompt_empty(self):
        p = get_profile("financial_rfp")
        assert p.llamaparse_system_prompt == ""
