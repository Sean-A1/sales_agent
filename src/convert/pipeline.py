"""
Conversion pipeline entry point.

Phase 1 stub — structure only, no processing yet.
Subsequent phases will add parse → metadata → clean → export stages.
"""
from __future__ import annotations

from pathlib import Path

from rich.console import Console

console = Console()


def run_convert(
    input_dir: Path,
    output_dir: Path,
    profile_name: str,
    debug: bool = False,
) -> None:
    """Orchestrate the full PDF conversion pipeline (stub)."""
    console.print(
        f"[yellow]convert: not yet implemented.[/yellow]\n"
        f"  input_dir  : {input_dir}\n"
        f"  output_dir : {output_dir}\n"
        f"  profile    : {profile_name}\n"
        f"  debug      : {debug}"
    )
