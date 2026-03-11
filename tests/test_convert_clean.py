"""
Offline tests for the convert clean stage — no network / LLM calls.

Run with:
    poetry run pytest tests/test_convert_clean.py -v
"""
from __future__ import annotations

import pytest

from src.convert.clean import clean_markdown
from src.convert.profiles import get_profile


@pytest.fixture()
def profile():
    return get_profile("financial_rfp")


# ---------------------------------------------------------------------------
# get_profile
# ---------------------------------------------------------------------------

def test_get_profile_known():
    p = get_profile("financial_rfp")
    assert p.name == "financial_rfp"


def test_get_profile_unknown():
    with pytest.raises(ValueError, match="Unknown conversion profile"):
        get_profile("does_not_exist")


# ---------------------------------------------------------------------------
# remove_patterns
# ---------------------------------------------------------------------------

def test_removes_page_number_line(profile):
    md = "Some text.\n\nPage 3 of 12\n\nMore text."
    result = clean_markdown(md, profile)
    assert "Page 3 of 12" not in result
    assert "Some text." in result
    assert "More text." in result


def test_removes_dash_page_number(profile):
    md = "Section A.\n\n- 7 -\n\nSection B."
    result = clean_markdown(md, profile)
    assert "- 7 -" not in result


def test_removes_confidential_watermark(profile):
    md = "Proposal details.\n\nCONFIDENTIAL\n\nScope section."
    result = clean_markdown(md, profile)
    assert "CONFIDENTIAL" not in result


def test_removes_draft_watermark(profile):
    md = "Header.\n\nDRAFT\n\nBody."
    result = clean_markdown(md, profile)
    assert "DRAFT" not in result


# ---------------------------------------------------------------------------
# fix_hyphenation
# ---------------------------------------------------------------------------

def test_fixes_hyphenated_word(profile):
    md = "The require-\nment is clear."
    result = clean_markdown(md, profile)
    assert "requirement" in result


def test_does_not_join_intentional_sentence_hyphen(profile):
    # A hyphen not followed by a word character on the next line is left alone.
    md = "End of sentence-\n\nNew paragraph."
    result = clean_markdown(md, profile)
    # The hyphen before a blank line should not be joined
    assert "-" in result


# ---------------------------------------------------------------------------
# normalize_whitespace
# ---------------------------------------------------------------------------

def test_collapses_excess_blank_lines(profile):
    md = "A\n\n\n\n\nB"
    result = clean_markdown(md, profile)
    assert "\n\n\n" not in result
    assert "A" in result
    assert "B" in result


def test_preserves_single_blank_line(profile):
    md = "A\n\nB"
    result = clean_markdown(md, profile)
    assert result == "A\n\nB"


def test_strips_leading_trailing_whitespace(profile):
    md = "\n\n  Hello world.  \n\n"
    result = clean_markdown(md, profile)
    assert result == "Hello world."


# ---------------------------------------------------------------------------
# table content is not disturbed
# ---------------------------------------------------------------------------

def test_table_rows_preserved(profile):
    md = (
        "| Col A | Col B |\n"
        "| ----- | ----- |\n"
        "| val 1 | val 2 |\n"
    )
    result = clean_markdown(md, profile)
    assert "| Col A | Col B |" in result
    assert "| val 1 | val 2 |" in result
