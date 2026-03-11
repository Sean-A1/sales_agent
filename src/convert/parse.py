"""
PDF parse stage — wraps LlamaParse for batch processing.

All PDFs in the batch share a single LlamaParse instance configured from the
active conversion profile. Results are returned as raw markdown strings.
"""
from __future__ import annotations

from pathlib import Path

from rich.console import Console

from .profiles.base import ConversionProfile

console = Console()


def parse_pdfs(
    pdf_paths: list[Path],
    profile: ConversionProfile,
    api_key: str,
    *,
    debug: bool = False,
) -> dict[Path, str]:
    """Parse a batch of PDFs with LlamaParse; return {pdf_path: raw_markdown}."""
    from llama_parse import LlamaParse  # deferred so import errors surface clearly

    parser = LlamaParse(
        api_key=api_key,
        result_type="markdown",
        system_prompt=profile.llamaparse_instructions,
        verbose=debug,
    )

    results: dict[Path, str] = {}
    for pdf_path in pdf_paths:
        console.print(f"  parsing [cyan]{pdf_path.name}[/cyan] …")
        documents = parser.load_data(str(pdf_path))
        text = "\n\n".join(doc.text for doc in documents).strip()
        if not text:
            raise RuntimeError(
                f"LlamaParse returned empty content for '{pdf_path.name}'. "
                "Check your API key and that the file is a valid PDF."
            )
        results[pdf_path] = text

    return results
