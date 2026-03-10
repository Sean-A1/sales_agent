"""
Smoke tests – no network / LLM calls required.

Run with:
    poetry run pytest tests/test_smoke.py -v
"""
from pathlib import Path


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------

def test_config_loads():
    """Config module can be imported and ROOT_DIR resolves to an existing dir."""
    from src.rag.config import (
        CHUNK_SIZE,
        EMBEDDING_MODEL,
        INDEX_DIR,
        MAX_CHUNK_CHARS,
        MAX_CONTEXT_CHUNKS,
        MAX_QUERY_CHARS,
        MAX_TOKENS,
        PDF_DIR,
        ROOT_DIR,
        TEMPERATURE,
        TOP_K,
    )

    assert ROOT_DIR.exists(), f"ROOT_DIR does not exist: {ROOT_DIR}"
    assert CHUNK_SIZE > 0
    assert TOP_K > 0
    assert MAX_CONTEXT_CHUNKS > 0
    assert MAX_CHUNK_CHARS > 0
    assert MAX_QUERY_CHARS > 0
    assert MAX_TOKENS > 0
    assert 0.0 <= TEMPERATURE <= 2.0
    assert isinstance(EMBEDDING_MODEL, str) and EMBEDDING_MODEL


def test_paths_exist():
    """data/pdf directory exists (PDFs should be placed there)."""
    from src.rag.config import PDF_DIR

    assert PDF_DIR.exists(), f"PDF directory not found: {PDF_DIR}"


# ---------------------------------------------------------------------------
# utils
# ---------------------------------------------------------------------------

def test_truncate_text_short():
    from src.rag.utils import truncate_text

    assert truncate_text("hello", 100) == "hello"


def test_truncate_text_long():
    from src.rag.utils import truncate_text

    result = truncate_text("a" * 2000, 100)
    assert result.endswith("…")
    assert len(result) == 101  # 100 chars + "…" (1 char, U+2026)


def test_truncate_query():
    from src.rag.utils import truncate_query

    long_q = "?" * 1000
    result = truncate_query(long_q, 500)
    assert len(result) <= 502
    assert result.endswith("…")


def test_limit_chunks_count():
    from langchain.schema import Document

    from src.rag.utils import limit_chunks

    docs = [
        Document(page_content="x" * 100, metadata={"source": "test", "page": i})
        for i in range(10)
    ]
    limited = limit_chunks(docs, max_chunks=3, max_chars=500)
    assert len(limited) == 3


def test_limit_chunks_truncates_content():
    from langchain.schema import Document

    from src.rag.utils import limit_chunks

    docs = [
        Document(page_content="y" * 2000, metadata={"source": "test", "page": 0})
    ]
    limited = limit_chunks(docs, max_chunks=4, max_chars=500)
    assert len(limited) == 1
    assert len(limited[0].page_content) <= 502  # 500 + "…"
    assert limited[0].page_content.endswith("…")


def test_limit_chunks_preserves_metadata():
    from langchain.schema import Document

    from src.rag.utils import limit_chunks

    docs = [
        Document(
            page_content="hello world",
            metadata={"source": "test.pdf", "page": 3},
        )
    ]
    limited = limit_chunks(docs, max_chunks=4, max_chars=500)
    assert limited[0].metadata["source"] == "test.pdf"
    assert limited[0].metadata["page"] == 3


def test_format_chunks_for_display():
    from langchain.schema import Document

    from src.rag.utils import format_chunks_for_display

    docs = [
        Document(
            page_content="Sample content for display.",
            metadata={"source": "doc.pdf", "page": 1},
        )
    ]
    output = format_chunks_for_display(docs)
    assert "[1]" in output
    assert "doc.pdf" in output
    assert "Sample content" in output


def test_format_chunks_no_ellipsis_for_short_content():
    from langchain.schema import Document

    from src.rag.utils import format_chunks_for_display

    doc = Document(page_content="Short.", metadata={"source": "brief.pdf", "page": 0})
    output = format_chunks_for_display([doc])
    assert "brief.pdf" in output
    assert "Short." in output
    assert "…" not in output
