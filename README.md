# PDF RAG — LlamaParse + Chroma + LangChain + OpenAI

Local PDF question-answering pipeline.
Drop PDFs in `data/pdf/`, run `ingest`, then `query`.
Works without an RAG_OPENAI_API_KEY (returns raw retrieved chunks instead of an LLM answer).

---

## Stack

| Layer | Library |
|---|---|
| PDF parsing | LlamaParse (primary) · PyPDFLoader (fallback) |
| Chunking | LangChain `RecursiveCharacterTextSplitter` |
| Embeddings | `sentence-transformers` · `all-MiniLM-L6-v2` (local) |
| Vector store | Chroma (persisted to `data/index/`) |
| LLM | `ChatOpenAI` via `langchain-openai` (optional) |
| CLI | Typer + Rich |

---

## Installation

This project is developed inside WSL.

```bash
# If needed, point Poetry to Python 3.11 first
poetry env use /home/laptop_wsl/.local/bin/python3.11

# Install dependencies
poetry install
```

---

## Environment variables (`.env`)

Copy `.env.example` → `.env` and fill in your keys.

```ini
# Required for PDF parsing
LLAMAPARSE_API_KEY=lx-...          # or LLAMA_CLOUD_API_KEY (fallback)

# Optional – enables LLM answers; absent → chunks-only mode
RAG_OPENAI_API_KEY=sk-...
```

Full list of overridable settings is in `.env.example`.

---

## Usage (WSL / bash)

### 1. Place PDFs

```bash
# PDFs are already in the repo sample folder, or add your own:
cp /path/to/report.pdf data/pdf/
```

### 2. Ingest (first time or after adding new PDFs)

```bash
# Normal ingest (adds to existing index)
python main.py ingest

# Wipe index and rebuild from scratch
python main.py ingest --reset
```

Output example:
```
[ingest] Found 10 PDF file(s) in data/pdf
...
[ingest] Done. Index persisted at data/index
```

### 3. Query

```bash
# Basic query (LLM answer if RAG_OPENAI_API_KEY is set)
python main.py query "사업의 주요 요구사항은 무엇인가요?"

# Override top-k and chunk limits on the fly
python main.py query "주요 납품 일정은?" --top-k 5 --max-chunks 3 --max-chars 800

# Disable automatic query truncation
python main.py query "very long question ..." --no-truncate
```

---

## Token / cost control policy

All limits have sensible defaults and can be overridden via `.env` or CLI flags.

| Setting | Default | Purpose |
|---|---|---|
| `MAX_TOKENS` | 256 | Hard cap on LLM response length |
| `TEMPERATURE` | 0.1 | Low = deterministic, fewer wasted tokens |
| `TOP_K` | 4 | Chunks fetched from vector store |
| `MAX_CONTEXT_CHUNKS` | 4 | Chunks actually forwarded to LLM |
| `MAX_CHUNK_CHARS` | 1 200 | Each chunk is truncated before LLM call |
| `MAX_QUERY_CHARS` | 500 | Long questions are trimmed (no LLM cost) |

### How to adjust

```ini
# .env
MAX_TOKENS=128          # even cheaper responses
MAX_CHUNK_CHARS=800     # smaller context window
TOP_K=3                 # retrieve fewer chunks
```

Or pass `--max-chunks` / `--max-chars` / `--top-k` directly to the `query` command.

---

## No-LLM mode

If `RAG_OPENAI_API_KEY` is not set the pipeline skips the LLM entirely and prints
the retrieved document chunks in a readable format:

```
[1] source='data/pdf/01_NPS_RFP_Sample.pdf'  page=4
    사업 개요: 국민연금공단은 차세대 IT 시스템 구축을 위해 …
```

This is useful for:
- Validating that ingest worked correctly
- Inspecting retrieval quality without spending tokens
- Running the tool with no API keys at all

---

## Running tests

```bash
poetry run pytest tests/ -v
```

Smoke tests cover config loading, chunk truncation, and utility functions.
No network calls are made during tests.

---

## Troubleshooting

### API key not found
```
ValueError: LLAMAPARSE_API_KEY / LLAMA_CLOUD_API_KEY not set
```
→ Make sure `.env` exists in the project root and contains the key.
   Both `LLAMAPARSE_API_KEY` and `LLAMA_CLOUD_API_KEY` are accepted.

### LlamaParse fails, falling back
```
[warn] LlamaParse failed for 'file.pdf' (...) – switching to PyPDFLoader
```
→ Normal behaviour. PyPDFLoader is used automatically.
   LlamaParse may fail on malformed PDFs or network issues.

### Index not found
```
[error] Index not found at data/index. Run 'python main.py ingest' first.
```
→ Run `python main.py ingest` at least once before querying.

### Permission error on `data/index`
→ Make sure your user has write access to the project folder.
   On Windows, try running PowerShell as Administrator, or change `INDEX_DIR` in `.env`.

### Chroma / embedding first run is slow
→ `sentence-transformers` downloads the model weights on first use (~90 MB).
   Subsequent runs use the cached model from `~/.cache/huggingface/`.


### Poetry rejects the current Python version

This project currently requires Python `>=3.11,<3.12`.

On Ubuntu 24.04 / WSL, the default system Python may be 3.12.
If needed, install Python 3.11 separately and point Poetry to it:

```bash
poetry env use /home/laptop_wsl/.local/bin/python3.11
poetry install
```