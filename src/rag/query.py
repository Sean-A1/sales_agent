"""
Query pipeline: question → retrieve chunks → (LLM answer | chunks display).

Cost-control measures applied at every call:
  - Query is trimmed to MAX_QUERY_CHARS before any search.
  - Only top MAX_CONTEXT_CHUNKS chunks are forwarded to the LLM.
  - Each chunk is truncated to MAX_CHUNK_CHARS characters.
  - LLM is called with max_tokens=MAX_TOKENS, temperature=TEMPERATURE.

If OPENAI_API_KEY is absent, the pipeline skips the LLM and prints the
retrieved chunks directly (useful for testing without spending tokens).
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from . import config
from .prompts import QA_PROMPT
from .utils import format_chunks_for_display, limit_chunks, truncate_query

console = Console()


def _get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)


def run_query(
    question: str,
    index_dir: Path = config.INDEX_DIR,
    top_k: int = config.TOP_K,
    max_chunk_chars: int = config.MAX_CHUNK_CHARS,
    max_context_chunks: int = config.MAX_CONTEXT_CHUNKS,
    truncate_question: bool = True,
) -> str:
    """
    Execute a RAG query.

    Returns:
        The LLM answer string, or "" when running in no-LLM mode.
    """
    # ---- trim long queries ----
    if truncate_question and len(question) > config.MAX_QUERY_CHARS:
        question = truncate_query(question, config.MAX_QUERY_CHARS)
        console.print(
            f"[yellow][warn] Query truncated to {config.MAX_QUERY_CHARS} chars[/yellow]"
        )

    # ---- load vector store ----
    if not index_dir.exists():
        console.print(
            f"[red][error] Index not found at {index_dir}. "
            "Run 'python main.py ingest' first.[/red]"
        )
        return ""

    embeddings = _get_embeddings()
    db = Chroma(
        persist_directory=str(index_dir),
        embedding_function=embeddings,
    )
    retriever = db.as_retriever(search_kwargs={"k": top_k})

    # ---- retrieve ----
    raw_docs: List[Document] = retriever.invoke(question)

    # ---- hard-limit context budget ----
    docs = limit_chunks(raw_docs, max_chunks=max_context_chunks, max_chars=max_chunk_chars)

    console.print(
        f"[dim]Retrieved {len(raw_docs)} chunk(s) → "
        f"using top {len(docs)} (≤{max_chunk_chars} chars each)[/dim]"
    )

    # ====================================================================
    # No-LLM mode  (OPENAI_API_KEY not set)
    # ====================================================================
    if not config.OPENAI_API_KEY:
        console.print(
            Panel(
                "[yellow]OPENAI_API_KEY not set – showing retrieved chunks only.[/yellow]\n"
                "Set OPENAI_API_KEY in .env to enable LLM answers.",
                title="RAG: Chunks-Only Mode",
                border_style="yellow",
            )
        )
        console.print(format_chunks_for_display(docs))
        return ""

    # ====================================================================
    # LLM mode
    # ====================================================================
    from langchain_openai import ChatOpenAI  # type: ignore

    llm = ChatOpenAI(
        api_key=config.OPENAI_API_KEY,
        model=config.OPENAI_MODEL,
        max_tokens=config.MAX_TOKENS,
        temperature=config.TEMPERATURE,
    )

    context = "\n\n---\n\n".join(d.page_content for d in docs)
    chain = QA_PROMPT | llm

    console.print(
        f"[dim]Querying {config.OPENAI_MODEL} "
        f"(max_tokens={config.MAX_TOKENS}, temp={config.TEMPERATURE}) …[/dim]"
    )

    response = chain.invoke({"context": context, "question": question})
    answer: str = (
        response.content if hasattr(response, "content") else str(response)
    )

    console.print(Panel(Markdown(answer), title="Answer", border_style="green"))
    return answer
