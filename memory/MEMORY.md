# Project Memory: langchain-pdf-rag

## Purpose
Python + LangChain PDF RAG pipeline. LlamaParse (primary) + PyPDFLoader (fallback) → Chroma → OpenAI.

## Key paths
- Entry point: `main.py` (project root)
- CLI: `src/app/cli.py` (typer, commands: ingest / query)
- Config: `src/rag/config.py` (all env-var knobs)
- Loader: `src/rag/loaders.py` (LlamaParse → PyPDFLoader fallback)
- Ingest: `src/rag/ingest.py`
- Query: `src/rag/query.py`
- Utils: `src/rag/utils.py` (truncate_text, limit_chunks, format_chunks_for_display)
- PDFs: `data/pdf/` (10 Korean RFP sample PDFs already present)
- Index: `data/index/` (gitignored, Chroma persist dir)

## Cost-control defaults
MAX_TOKENS=256, TEMPERATURE=0.1, TOP_K=4, MAX_CONTEXT_CHUNKS=4, MAX_CHUNK_CHARS=1200, MAX_QUERY_CHARS=500

## Dependencies (key)
- langchain=^0.3.0, langchain-community=^0.3.0, langchain-openai>=0.2.0,<0.4.0
- langchain-chroma=^0.1.0 (added), chromadb=^0.5.0
- sentence-transformers=^3.0.0 (local embeddings, all-MiniLM-L6-v2)
- llama-parse=^0.5.0, pypdf>=4.2.0
- typer=^0.12.0, rich=^13.0.0, tqdm=^4.66.0

## Env vars
- LLAMAPARSE_API_KEY (preferred) or LLAMA_CLOUD_API_KEY (fallback)
- OPENAI_API_KEY (optional; absent → chunks-only mode)

## Confirmed working (2026-03-04)
- ingest: 10 PDFs → 30 pages → 69 chunks, Chroma persisted ✓
- query: LLM answer returned ✓ (Korean garbling is terminal encoding, not a bug)
- LlamaParse auth failed → silently returns [] → fallback to PyPDFLoader ✓

## Known fixes applied
1. typer `"--reset/--no-reset"` → `is_flag=True` (typer 0.12→0.15 compatibility)
2. Typer upgraded: `^0.12.0` → `^0.15.0` (click 8.3 incompatibility)
3. `opentelemetry-exporter-otlp-proto-grpc` force-upgraded 1.11.1→1.39.1 via pip (protobuf 7.x compatibility; chromadb 0.5.23 pins old version)
4. `Chroma.from_documents()` → `Chroma() + db.add_documents()` (empty-batch error)
5. LlamaParse fallback: check empty result (not just exception) → call PyPDFLoader
6. `ANONYMIZED_TELEMETRY=False` in config.py (suppress harmless chromadb warnings)
7. Chroma import: `langchain_community.vectorstores` → `langchain_chroma`

## Post-install manual step needed
After `poetry install`, must run:
```
poetry run pip install "opentelemetry-exporter-otlp-proto-grpc>=1.39.0" "opentelemetry-proto>=1.39.0" --upgrade
```
(chromadb 0.5.23 pins 1.11.1 which is incompatible with protobuf 7.x)

## Run commands
```powershell
poetry install
poetry shell
python main.py ingest --reset
python main.py query "질문"
poetry run pytest tests/ -v
```

## pytest config
pyproject.toml has `[tool.pytest.ini_options] pythonpath = ["."]` so `src.*` imports work.
