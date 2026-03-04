"""
Typer-based CLI for the PDF RAG pipeline.

Commands
--------
  ingest   Load PDFs → chunk → embed → persist to Chroma
  query    Ask a question against the Chroma index

Run from the project root:
  python main.py ingest [OPTIONS]
  python main.py query  QUESTION [OPTIONS]
"""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(
    name="rag",
    add_completion=False,
    help="PDF RAG CLI — LlamaParse + Chroma + OpenAI",
)
console = Console()


# ---------------------------------------------------------------------------
# ingest command
# ---------------------------------------------------------------------------

@app.command()
def ingest(
    pdf_dir: Path = typer.Option(
        None,
        "--pdf-dir", "-p",
        help="Directory containing .pdf files  [default: data/pdf]",
    ),
    index_dir: Path = typer.Option(
        None,
        "--index-dir", "-i",
        help="Chroma persist directory  [default: data/index]",
    ),
    reset: bool = typer.Option(
        False,
        "--reset",
        is_flag=True,
        help="Wipe existing index before ingesting",
    ),
) -> None:
    """Load PDFs → chunk → embed → persist to Chroma."""
    from src.rag import config as cfg
    from src.rag.ingest import run_ingest

    run_ingest(
        pdf_dir=pdf_dir or cfg.PDF_DIR,
        index_dir=index_dir or cfg.INDEX_DIR,
        reset=reset,
    )


# ---------------------------------------------------------------------------
# query command
# ---------------------------------------------------------------------------

@app.command()
def query(
    question: str = typer.Argument(..., help="Question to ask"),
    top_k: int = typer.Option(
        None,
        "--top-k", "-k",
        help="Chunks to retrieve from the vector store  [default: TOP_K env]",
    ),
    index_dir: Path = typer.Option(
        None,
        "--index-dir", "-i",
        help="Chroma persist directory  [default: data/index]",
    ),
    max_chars: int = typer.Option(
        None,
        "--max-chars",
        help="Max chars per context chunk  [default: MAX_CHUNK_CHARS env]",
    ),
    max_chunks: int = typer.Option(
        None,
        "--max-chunks",
        help="Max context chunks sent to LLM  [default: MAX_CONTEXT_CHUNKS env]",
    ),
    no_truncate: bool = typer.Option(
        False,
        "--no-truncate",
        help="Disable automatic query truncation",
    ),
) -> None:
    """Query the vector store and return an answer (or top-k chunks if no API key)."""
    from src.rag import config as cfg
    from src.rag.query import run_query

    run_query(
        question=question,
        index_dir=index_dir or cfg.INDEX_DIR,
        top_k=top_k or cfg.TOP_K,
        max_chunk_chars=max_chars or cfg.MAX_CHUNK_CHARS,
        max_context_chunks=max_chunks or cfg.MAX_CONTEXT_CHUNKS,
        truncate_question=not no_truncate,
    )


if __name__ == "__main__":
    app()
