"""
financial_rfp — conversion profile for financial / institutional RFP documents.

Assumptions:
  - Mostly text and tables; image captions are not a priority in v1.
  - Documents follow a formal RFP structure with header metadata and
    a deadline/contact block near the end.
"""
from __future__ import annotations

from .base import ConversionProfile

FINANCIAL_RFP_METADATA_PROMPT = """\
You are a document metadata extractor. You will receive the opening section \
and closing section of a financial or institutional Request for Proposal (RFP).

Extract the following fields and return ONLY a valid JSON object with these keys:
{schema_description}

If a field cannot be determined from the text, use null.

--- OPENING SECTION ---
{header}

--- CLOSING SECTION ---
{footer}

Return only the JSON object, no explanation.
"""

financial_rfp = ConversionProfile(
    name="financial_rfp",

    # -----------------------------------------------------------------------
    # Parse
    # -----------------------------------------------------------------------
    llamaparse_instructions=(
        "This document is a financial or institutional Request for Proposal (RFP). "
        "Preserve all table structures as markdown tables. "
        "Preserve section headings using markdown heading syntax. "
        "Do not summarise or omit any text. "
        "Treat multi-column layouts by reading left-to-right, top-to-bottom."
    ),

    # -----------------------------------------------------------------------
    # Clean
    # -----------------------------------------------------------------------
    remove_patterns=[
        r"(?m)^\s*Page\s+\d+\s+of\s+\d+\s*$",   # "Page 3 of 12" lines
        r"(?m)^\s*-\s*\d+\s*-\s*$",              # "- 3 -" page number style
        r"(?m)^CONFIDENTIAL\s*$",                 # standalone watermark lines
        r"(?m)^DRAFT\s*$",                        # standalone draft watermark lines
    ],
    normalize_whitespace=True,
    fix_hyphenation=True,
    preserve_table_blocks=True,
    reconstitute_title_institution=True,

    # -----------------------------------------------------------------------
    # Metadata
    # -----------------------------------------------------------------------
    metadata_schema={
        "issuer":        "Organisation or government body issuing the RFP",
        "title":         "Official title of the RFP document",
        "reference":     "RFP or tender reference / document number",
        "issue_date":    "Date the RFP was published (ISO 8601 if possible)",
        "deadline":      "Submission deadline (ISO 8601 if possible)",
        "contact_name":  "Primary contact person name",
        "contact_email": "Primary contact email address",
        "scope_summary": "One-sentence summary of the procurement scope",
        "value":         "Estimated contract value or budget (as stated, or null)",
    },
    metadata_prompt_template=FINANCIAL_RFP_METADATA_PROMPT,
)
