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

# Matches a Korean (or mixed) key followed by colon and a value.
# Key: short label (1-20 chars, Korean/alpha/spaces/parens/slashes).
_HEADER_KV_RE = re.compile(
    r"^([가-힣A-Za-z\s/()·\d]+\S):\s*(.+)$",
)

# Standalone Clause ID heading: # [PREFIX-N.N] or # [PREFIX-N.N.N]
_CLAUSE_ID_HEADING_RE = re.compile(r"^# (\[[A-Z]+-[\d.]+\])\s*$")
# Numbered section heading that should be preserved: # 1. Title, # 부록 A.
_NUMBERED_SECTION_RE = re.compile(r"^# (?:\d+\.|부록)")


def _reconstitute_title_institution(text: str) -> str:
    """Prepend institution name to the first H1 if split into a '기관:' line."""
    m = _INSTITUTION_AFTER_H1.search(text)
    if not m:
        return text
    h1_line = m.group(1)        # e.g. "# 국내주식 액티브 … RFP"
    institution = m.group(2).strip()  # e.g. "국민연금 기금운용본부(가상)"
    new_h1 = f"# {institution} | {h1_line[2:]}"
    return text[:m.start()] + new_h1 + text[m.start() + len(h1_line):]


def _convert_header_kvs_to_table(text: str) -> str:
    """Convert consecutive key: value lines after the first H1 into a md table.

    LlamaParse often flattens the PDF summary table at the top of a document
    into plain ``key: value`` lines.  This function detects such blocks and
    re-formats them as a proper markdown table so the structure is preserved.
    """
    # Locate the first H1 line.
    h1_match = re.search(r"^# .+$", text, re.MULTILINE)
    if not h1_match:
        return text

    after_h1 = h1_match.end()
    remaining = text[after_h1:]

    # Walk through lines after the H1, collecting key-value pairs.
    kvs: list[tuple[str, str]] = []
    consumed = 0  # how many chars of `remaining` belong to the KV block

    for line in remaining.split("\n"):
        stripped = line.strip()
        if not stripped:
            # blank line — skip but keep consuming
            consumed += len(line) + 1  # +1 for the '\n'
            continue
        m = _HEADER_KV_RE.match(stripped)
        if m and len(m.group(1)) <= 20:
            kvs.append((m.group(1).strip(), m.group(2).strip()))
            consumed += len(line) + 1
        else:
            # First non-blank, non-KV line → end of block
            break

    if len(kvs) < 2:
        return text

    # Build the markdown table.
    table_lines = ["| 항목 | 내용 |", "| --- | --- |"]
    for key, value in kvs:
        k = key.replace("|", "\\|")
        v = value.replace("|", "\\|")
        table_lines.append(f"| {k} | {v} |")
    table_str = "\n".join(table_lines)

    # Replace the original KV block with the table.
    return text[:after_h1] + "\n\n" + table_str + "\n\n" + remaining[consumed:]


def _fix_clause_id_headings(text: str) -> str:
    """Fix Clause ID lines that LlamaParse incorrectly promoted to H1 headings.

    Pattern 1 – standalone ``# [CLAUSE-ID]`` heading:
        Merge the clause ID prefix with the next non-empty, non-heading line.
    Pattern 2 – heading within a list-item context:
        If a non-numbered ``# text`` line appears right after list items,
        demote it back to a list item (the original formatting).
    """
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        stripped = lines[i].strip()

        # --- Pattern 1: # [CLAUSE-ID] standalone → merge with next text ---
        m = _CLAUSE_ID_HEADING_RE.match(stripped)
        if m:
            clause_id = m.group(1)
            # Find the next non-empty line
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j < n and not lines[j].strip().startswith("#"):
                out.append(f"{clause_id} {lines[j].strip()}")
                i = j + 1
            else:
                # Next line is a heading or EOF — just remove the '#'
                out.append(clause_id)
                i += 1
            continue

        # --- Pattern 2: heading right after list items → demote to list item ---
        if (
            stripped.startswith("# ")
            and not _NUMBERED_SECTION_RE.match(stripped)
        ):
            # Find the last non-empty line in output
            prev = ""
            for k in range(len(out) - 1, -1, -1):
                if out[k].strip():
                    prev = out[k].strip()
                    break
            if prev.startswith("- "):
                out.append(f"- {stripped[2:]}")
                i += 1
                continue

        out.append(lines[i])
        i += 1

    return "\n".join(out)


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

    # 4. Convert header key-value lines into a markdown table.
    if profile.preserve_table_blocks:
        text = _convert_header_kvs_to_table(text)

    # 5. Fix Clause ID headings promoted by LlamaParse.
    if profile.fix_clause_id_headings:
        text = _fix_clause_id_headings(text)

    # 6. Collapse runs of 3+ blank lines to 2 blank lines.
    #    preserve_table_blocks is respected implicitly: markdown table rows
    #    (lines starting with "|") never contain internal blank lines, so
    #    standard 3→2 collapsing does not disturb table formatting.
    if profile.normalize_whitespace:
        text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
