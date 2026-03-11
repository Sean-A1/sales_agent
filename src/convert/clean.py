"""
Markdown clean stage.

Applies profile-driven normalisation rules to raw markdown returned by
the parse stage. No LLM calls — pure text transformations.
"""
from __future__ import annotations

import re

from .profiles.base import ConversionProfile


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

    # 3. Collapse runs of 3+ blank lines to 2 blank lines.
    #    preserve_table_blocks is respected implicitly: markdown table rows
    #    (lines starting with "|") never contain internal blank lines, so
    #    standard 3→2 collapsing does not disturb table formatting.
    if profile.normalize_whitespace:
        text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
