"""
Conversion pipeline — Phase 2: parse + clean + md export.

Stages:
  1. Resolve profile (financial_rfp only for now)
  2. Discover PDFs in input_dir
  3. Parse with LlamaParse (one shared parser instance for the batch)
  4. Clean each raw markdown via the profile's normalisation rules
  5. Write cleaned markdown to output_dir/md/<stem>.md
"""
from __future__ import annotations

from pathlib import Path

from rich.console import Console

from . import config as cfg
from .clean import clean_markdown
from .parse import parse_pdfs
from .profiles import get_profile

console = Console()


def run_convert(
    input_dir: Path,
    output_dir: Path,
    profile_name: str,
    debug: bool = False,
) -> None:
    """Orchestrate the PDF → markdown conversion pipeline."""

    # 1. Resolve profile — raises ValueError for unknown names
    profile = get_profile(profile_name)

    # 2. Discover PDFs
    pdf_paths = sorted(input_dir.glob("*.pdf"))
    if not pdf_paths:
        console.print(f"[yellow]No PDFs found in {input_dir}[/yellow]")
        return

    console.print(
        f"[bold]convert[/bold]: profile=[cyan]{profile_name}[/cyan]  "
        f"files={len(pdf_paths)}  output={output_dir}"
    )

    # 3. Validate API key before making any network calls
    if not cfg.LLAMAPARSE_API_KEY:
        console.print(
            "[red]Error:[/red] LLAMAPARSE_API_KEY (or LLAMA_CLOUD_API_KEY) is not set."
        )
        raise SystemExit(1)

    # 4. Parse — one LlamaParse instance shared across the batch
    raw_mds = parse_pdfs(pdf_paths, profile, cfg.LLAMAPARSE_API_KEY, debug=debug)

    # 5. Clean + write (only files that parsed successfully)
    md_dir = output_dir / "md"
    md_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for pdf_path, raw_md in raw_mds.items():
        cleaned = clean_markdown(raw_md, profile)
        if not cleaned.strip():
            console.print(
                f"  [yellow]skip[/yellow] {pdf_path.name} — cleaning produced empty output"
            )
            continue
        out_path = md_dir / f"{pdf_path.stem}.md"
        out_path.write_text(cleaned, encoding="utf-8")
        console.print(f"  [green]wrote[/green] {out_path}")
        written += 1

    if written == 0:
        console.print("[red]No files written.[/red]")
        raise SystemExit(1)

    console.print(
        f"\n[bold green]Done.[/bold green] "
        f"{written} file(s) written to [cyan]{md_dir}[/cyan]"
    )
