"""
Conversion pipeline configuration.

Reads directly from the environment — no imports from src.rag.
Override any value via .env or shell environment variables.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR   = Path(__file__).resolve().parent.parent.parent
DATA_DIR   = ROOT_DIR / "data"

CONVERT_INPUT_DIR  = DATA_DIR / "input" / "pdf"
CONVERT_EXPORT_DIR = DATA_DIR / "export"

# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
DEFAULT_PROFILE = os.getenv("CONVERT_PROFILE", "financial_rfp")

# ---------------------------------------------------------------------------
# API keys  (same env vars as RAG runtime; read independently here)
# ---------------------------------------------------------------------------
LLAMAPARSE_API_KEY     = os.getenv("LLAMAPARSE_API_KEY") or os.getenv("LLAMA_CLOUD_API_KEY") or ""
CONVERT_OPENAI_API_KEY = os.getenv("RAG_OPENAI_API_KEY") or ""
OPENAI_MODEL           = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
