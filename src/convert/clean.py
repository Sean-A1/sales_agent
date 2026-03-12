"""
Markdown clean stage.

Applies profile-driven normalisation rules to raw markdown returned by
the parse stage. No LLM calls — pure text transformations.
"""
from __future__ import annotations

import re

from .profiles.base import ConversionProfile


_INSTITUTION_AFTER_H1 = re.compile(
    r"^(# .+)\n\n기관:\s*(.+)$",
    re.MULTILINE,
)


def _reconstitute_title_institution(text: str) -> str:
    """Prepend institution name to the first H1 if split into a '기관:' line."""
    m = _INSTITUTION_AFTER_H1.search(text)
    if not m:
        return text
    h1_line = m.group(1)        # e.g. "# 국내주식 액티브 … RFP"
    institution = m.group(2).strip()  # e.g. "국민연금 기금운용본부(가상)"
    new_h1 = f"# {institution} | {h1_line[2:]}"
    return text[:m.start()] + new_h1 + text[m.start() + len(h1_line):]


def clean_markdown(raw_md: str, profile: ConversionProfile) -> str:
    """Return cleaned markdown according to the profile's normalisation rules."""
    text = raw_md

    # 1. Remove noise patterns (page numbers, watermarks, etc.)
    for pattern in profile.remove_patterns:
        text = re.sub(pattern, "", text)

    # 2. Rejoin words broken across lines with a soft hyphen.
    #    e.g. "require-\nment" → "requirement"
    #    Only joins when both sides are word characters (\w) to avoid
    #    disturbing intentional hyphens at end-of-sentences.
    if profile.fix_hyphenation:
        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # 3. Reconstitute institution name into the H1 title.
    #    LlamaParse often splits "기관: <name>" onto a separate line after the
    #    first heading.  Detect this pattern and prepend the institution to H1.
    if profile.reconstitute_title_institution:
        text = _reconstitute_title_institution(text)

    # 4. Collapse runs of 3+ blank lines to 2 blank lines.
    #    preserve_table_blocks is respected implicitly: markdown table rows
    #    (lines starting with "|") never contain internal blank lines, so
    #    standard 3→2 collapsing does not disturb table formatting.
    if profile.normalize_whitespace:
        text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
