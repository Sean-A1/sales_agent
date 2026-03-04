"""
Text / chunk budget utilities.

All functions are pure Python with no network calls – they exist solely to
keep token / character costs under control before anything reaches the LLM.
"""
from __future__ import annotations

from typing import List

from langchain.schema import Document


# ---------------------------------------------------------------------------
# Low-level text helpers
# ---------------------------------------------------------------------------

def truncate_text(text: str, max_chars: int) -> str:
    """Return text trimmed to max_chars, appending '…' when cut."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…"


def truncate_query(query: str, max_chars: int) -> str:
    """Trim an overly long question without any LLM call."""
    return truncate_text(query, max_chars)


# ---------------------------------------------------------------------------
# Chunk-level budget helpers
# ---------------------------------------------------------------------------

def limit_chunks(
    docs: List[Document],
    max_chunks: int,
    max_chars: int,
) -> List[Document]:
    """
    Apply a hard budget to a list of retrieved chunks.

    1. Keeps at most *max_chunks* documents.
    2. Truncates each document's page_content to *max_chars* characters.

    Returns new Document objects; originals are not modified.
    """
    result: List[Document] = []
    for doc in docs[:max_chunks]:
        trimmed = truncate_text(doc.page_content, max_chars)
        result.append(Document(page_content=trimmed, metadata=doc.metadata))
    return result


# ---------------------------------------------------------------------------
# Display helpers (no-LLM mode)
# ---------------------------------------------------------------------------

def format_chunks_for_display(docs: List[Document]) -> str:
    """
    Pretty-format retrieved chunks for terminal output when no LLM is
    available.  Shows source path, page number, and a short text preview.
    """
    lines: List[str] = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "?")
        preview = doc.page_content[:300].replace("\n", " ")
        ellipsis = "…" if len(doc.page_content) > 300 else ""
        lines.append(
            f"[{i}] source={source!r}  page={page}\n"
            f"    {preview}{ellipsis}"
        )
    return "\n\n".join(lines)
