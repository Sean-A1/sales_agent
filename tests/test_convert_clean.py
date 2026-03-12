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

# ---------------------------------------------------------------------------
# reconstitute_title_institution
# ---------------------------------------------------------------------------

def test_reconstitute_title_institution(profile):
    md = (
        "# 국내주식 액티브(장기성장형) 위탁운용사 선정 위탁운용사 RFP\n\n"
        "기관: 국민연금 기금운용본부(가상)\n\n"
        "선정 목적: 위탁운용사 선정"
    )
    result = clean_markdown(md, profile)
    assert result.startswith(
        "# 국민연금 기금운용본부(가상) | 국내주식 액티브(장기성장형) 위탁운용사 선정 위탁운용사 RFP"
    )
    # The "기관" data should be preserved in the markdown table
    assert "| 기관 | 국민연금 기금운용본부(가상) |" in result


def test_reconstitute_title_no_institution_line(profile):
    md = "# Already Complete Title\n\nSome body text."
    result = clean_markdown(md, profile)
    assert result.startswith("# Already Complete Title")


# ---------------------------------------------------------------------------
# header key-value → markdown table
# ---------------------------------------------------------------------------

def test_header_kvs_converted_to_table(profile):
    md = (
        "# 위탁운용사 RFP\n\n"
        "기관: 국민연금\n\n"
        "선정 목적: 위탁운용사 선정\n\n"
        "투자 유형: 국내주식\n\n"
        "예상 위탁규모: 3,000억원\n\n"
        "# 1. 개요\n\nBody text."
    )
    result = clean_markdown(md, profile)
    assert "| 항목 | 내용 |" in result
    assert "| 기관 | 국민연금 |" in result
    assert "| 선정 목적 | 위탁운용사 선정 |" in result
    assert "| 투자 유형 | 국내주식 |" in result
    assert "| 예상 위탁규모 | 3,000억원 |" in result
    # Body after the KV block should be preserved
    assert "# 1. 개요" in result
    assert "Body text." in result


def test_header_kvs_single_kv_not_converted(profile):
    """A single key-value line should NOT be converted into a table."""
    md = "# Title\n\n기관: 국민연금\n\n# 1. 개요"
    result = clean_markdown(md, profile)
    # With reconstitute on, 기관 merges into H1; only 1 KV → no table
    assert "| 항목 |" not in result


# ---------------------------------------------------------------------------
# table content is not disturbed
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# fix_clause_id_headings
# ---------------------------------------------------------------------------

def test_clause_id_heading_merged_with_next_line(profile):
    """# [CLAUSE-ID] standalone heading → merge with following paragraph."""
    md = (
        "# 4. 책임투자(ESG)\n\n"
        "# [ESG-4.3]\n\n"
        "배제 기준 위반이 확인되는 경우 시정계획을 제출해야 합니다."
    )
    result = clean_markdown(md, profile)
    assert "# [ESG-4.3]" not in result
    assert "[ESG-4.3] 배제 기준 위반이 확인되는 경우" in result
    # Legitimate heading preserved
    assert "# 4. 책임투자(ESG)" in result


def test_multiple_clause_id_headings_fixed(profile):
    """Multiple standalone Clause ID headings are all fixed."""
    md = (
        "# 5. 평가 기준\n\n"
        "# [EVAL-5.1]\n\n"
        "평가는 총 100점 만점입니다.\n\n"
        "# [EVAL-5.3]\n\n"
        "필요 시 인터뷰를 요청할 수 있습니다."
    )
    result = clean_markdown(md, profile)
    assert "[EVAL-5.1] 평가는 총 100점 만점입니다." in result
    assert "[EVAL-5.3] 필요 시 인터뷰를 요청할 수 있습니다." in result
    assert "# 5. 평가 기준" in result


def test_heading_after_list_items_demoted(profile):
    """A heading appearing right after list items is demoted to list item."""
    md = (
        "- [EXCL-4.2.3] 중대 환경오염 기업\n"
        "- [EXCL-4.2.4] 아동노동 확인된 기업\n\n"
        "# 국제 제재 위반 리스크가 높은 기업\n\n"
        "# [ESG-4.3]\n\n"
        "배제 기준 위반이 확인되는 경우 시정계획 제출."
    )
    result = clean_markdown(md, profile)
    # Heading demoted to list item
    assert "- 국제 제재 위반 리스크가 높은 기업" in result
    assert "# 국제 제재" not in result
    # Clause ID heading merged with text
    assert "[ESG-4.3] 배제 기준 위반이 확인되는 경우" in result


def test_numbered_section_headings_preserved(profile):
    """Numbered section headings (# 1. Title) are never demoted."""
    md = (
        "- [DOC-3.3.8] 최근 3년 제재 내역\n\n"
        "# 4. 책임투자(ESG) 및 배제/금지 조건\n\n"
        "[ESG-4.1] 운용사는 ESG 리스크를 통합해야 합니다."
    )
    result = clean_markdown(md, profile)
    assert "# 4. 책임투자(ESG) 및 배제/금지 조건" in result


def test_appendix_heading_preserved(profile):
    """부록 headings are preserved."""
    md = (
        "- [DEL-6.2.5] ESG 관여 로그\n\n"
        "# 부록 A. 제안서 응답 템플릿\n\n"
        "내용"
    )
    result = clean_markdown(md, profile)
    assert "# 부록 A. 제안서 응답 템플릿" in result


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
