"""
Central configuration – loaded once at import time.
All tuneable knobs live here; override via .env or environment variables.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Suppress chromadb telemetry (avoids harmless "capture() takes 1 argument" warnings)
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("CHROMA_TELEMETRY", "False")

# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------
# LlamaParse: prefer LLAMAPARSE_API_KEY, fall back to LLAMA_CLOUD_API_KEY
LLAMAPARSE_API_KEY: str = (
    os.getenv("LLAMAPARSE_API_KEY") or os.getenv("LLAMA_CLOUD_API_KEY") or ""
)
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY") or ""

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR: Path = Path(__file__).resolve().parent.parent.parent
DATA_DIR: Path = ROOT_DIR / "data"
PDF_DIR: Path = DATA_DIR / "pdf"
INDEX_DIR: Path = DATA_DIR / "index"

# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))

# ---------------------------------------------------------------------------
# Retrieval / cost control  ← the most important knobs
# ---------------------------------------------------------------------------
# How many chunks the retriever fetches from the vector store
TOP_K: int = int(os.getenv("TOP_K", "4"))
# Hard cap: only this many chunks are actually sent to the LLM
MAX_CONTEXT_CHUNKS: int = int(os.getenv("MAX_CONTEXT_CHUNKS", "4"))
# Each chunk is truncated to this many characters before being sent
MAX_CHUNK_CHARS: int = int(os.getenv("MAX_CHUNK_CHARS", "1200"))
# Long queries are trimmed to this many characters (no LLM call for trimming)
MAX_QUERY_CHARS: int = int(os.getenv("MAX_QUERY_CHARS", "500"))

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "256"))
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))

# ---------------------------------------------------------------------------
# Embeddings  (local, no API key required)
# ---------------------------------------------------------------------------
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
