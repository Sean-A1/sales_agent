"""
ConversionProfile dataclass — the single source of document-type knowledge.

Each profile instance defines:
  - how LlamaParse should parse (instructions/prompt)
  - how clean.py should normalise the raw markdown
  - what metadata fields to extract and how to prompt the LLM
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConversionProfile:
    name: str

    # -----------------------------------------------------------------------
    # Parse stage
    # -----------------------------------------------------------------------
    llamaparse_instructions: str

    # -----------------------------------------------------------------------
    # Clean stage
    # -----------------------------------------------------------------------
    # Regex patterns whose matching lines are removed before export.
    remove_patterns: list[str] = field(default_factory=list)
    # Collapse runs of blank lines to a single blank line.
    normalize_whitespace: bool = True
    # Rejoin words split across lines with a hyphen (e.g. "require-\nment").
    fix_hyphenation: bool = True
    # Prevent whitespace normalization inside fenced table blocks.
    preserve_table_blocks: bool = True
    # Reconstitute the institution name into the H1 title when LlamaParse
    # splits "기관: <name>" onto a separate line after the heading.
    reconstitute_title_institution: bool = False
    # Fix Clause ID lines ([XXX-N.N]) that LlamaParse incorrectly promotes
    # to H1 headings, and list items that get turned into headings.
    fix_clause_id_headings: bool = False
    # Convert image tags (![alt](url)) to text placeholders ([IMAGE: alt]).
    convert_image_tags: bool = False

    # -----------------------------------------------------------------------
    # Metadata stage — single LLM sandwich call
    # -----------------------------------------------------------------------
    # Maps field name → plain-English description used in the LLM prompt.
    metadata_schema: dict[str, str] = field(default_factory=dict)
    # Prompt template; receives {header} (first ~2000 chars) and
    # {footer} (last ~1000 chars) of the raw parsed markdown.
    # Must instruct the model to return valid JSON only.
    metadata_prompt_template: str = ""
