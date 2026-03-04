"""
PDF loading with LlamaParse (primary) and PyPDFLoader (fallback).

Priority:
  1. LlamaParse   – rich markdown output, requires LLAMAPARSE_API_KEY
  2. PyPDFLoader  – always available, text-only
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from langchain.schema import Document

from . import config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LlamaParse loader
# ---------------------------------------------------------------------------

def _llamaparse_load(pdf_path: Path) -> List[Document]:
    """Load a single PDF via LlamaParse API (synchronous)."""
    from llama_parse import LlamaParse  # type: ignore

    api_key = config.LLAMAPARSE_API_KEY
    if not api_key:
        raise ValueError("LLAMAPARSE_API_KEY / LLAMA_CLOUD_API_KEY not set")

    parser = LlamaParse(
        api_key=api_key,
        result_type="markdown",
        verbose=False,
    )
    llama_docs = parser.load_data(str(pdf_path))

    docs: List[Document] = []
    for i, ld in enumerate(llama_docs):
        docs.append(
            Document(
                page_content=ld.text,
                metadata={"source": str(pdf_path), "page": i},
            )
        )
    logger.info("LlamaParse: %s → %d page(s)", pdf_path.name, len(docs))
    return docs


# ---------------------------------------------------------------------------
# PyPDF fallback loader
# ---------------------------------------------------------------------------

def _pypdf_load(pdf_path: Path) -> List[Document]:
    """Fallback: load PDF via LangChain PyPDFLoader."""
    from langchain_community.document_loaders import PyPDFLoader  # type: ignore

    loader = PyPDFLoader(str(pdf_path))
    docs = loader.load()
    logger.info("PyPDFLoader: %s → %d page(s)", pdf_path.name, len(docs))
    return docs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_pdf(pdf_path: Path) -> List[Document]:
    """
    Load a single PDF file.

    Tries LlamaParse first (if API key is present).
    Falls back to PyPDFLoader on any error OR empty result
    (LlamaParse silently returns [] on auth failure instead of raising).
    """
    if config.LLAMAPARSE_API_KEY:
        try:
            docs = _llamaparse_load(pdf_path)
            if docs:
                return docs
            logger.warning(
                "LlamaParse returned empty result for '%s' – switching to PyPDFLoader",
                pdf_path.name,
            )
        except Exception as exc:
            logger.warning(
                "LlamaParse failed for '%s' (%s) – switching to PyPDFLoader",
                pdf_path.name,
                exc,
            )
    return _pypdf_load(pdf_path)
