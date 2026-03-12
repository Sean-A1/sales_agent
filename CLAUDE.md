# CLAUDE.md

## Project

langchain_agent — PDF RAG pipeline + PDF convert pipeline.
Korean financial RFP documents. WSL + Poetry + Python 3.11.

## Repo Map

```
main.py                  # entrypoint
src/app/cli.py           # CLI (Typer + Rich)
src/rag/                 # RAG: ingest, query, loaders, prompts, config, utils
src/convert/             # Convert: parse → clean → metadata → export
  parse.py               # LlamaParse PDF → raw markdown
  clean.py               # markdown cleanup
  metadata.py            # LLM sandwich → YAML frontmatter
  export.py              # md/html/xml/json export
  pipeline.py            # orchestrator
  profiles/              # base.py, financial_rfp.py
tests/                   # test_smoke, test_convert_clean/metadata/export
data/input/pdf/          # source PDFs
data/export/             # timestamped output dirs
memory/                  # legacy project docs (MEMORY.md, WORKFLOW.md, etc.)
```

## Commands

```bash
# Run
poetry run python main.py ingest
poetry run python main.py query "질문"
poetry run python main.py convert --input-dir data/input/pdf

# Test
poetry run pytest tests/ -v

# Lint check (before commit)
poetry run python -c "import src; print('import ok')"
```

## Branch Policy

NEVER work directly on `main`. Always:
1. `git checkout main && git pull`
2. `git checkout -b claude/<task-name>`
3. Work → commit → review diff
4. User merges to main

## Key Rules

- **Minimal edits only.** Small, focused changes. No broad refactors unless explicitly requested.
- **No secrets in commits.** Never commit `.env`, tokens, or credentials.
- **API separation.** `RAG_OPENAI_API_KEY` is for app runtime (RAG/eval), NOT for agent CLI login.
- **LlamaParse key.** Use `LLAMA_CLOUD_API_KEY` (standardized). Old `LLAMAPARSE_API_KEY` had typo issues.
- **Poetry.** Always use `poetry run` prefix. Python 3.11 required.
- **Korean context.** PDFs and metadata are Korean financial RFPs. Keep Korean text handling in mind.

## Validation Before Commit

Run the smallest relevant check first:
1. Import check: `poetry run python -c "import src"`
2. Targeted test: `poetry run pytest tests/test_convert_clean.py -v`
3. Full suite: `poetry run pytest tests/ -v`
4. Review diff: `git diff --stat`

## Current Architecture Status

### RAG pipeline (stable)
LlamaParse → chunking → Chroma embeddings → LLM query (optional)

### Convert pipeline (active development)
Phase 1-4 complete. Known limitation: html/xml/json inherit fidelity issues from md.
**Next priority:** parse/clean quality (title structure, table fidelity, heading levels).

## What NOT to Do

- Don't rename `RAG_OPENAI_API_KEY` without explicit instruction
- Don't introduce unrelated dependency churn
- Don't make formatting-only changes unless requested
- Don't modify `.env` policy without explicit instruction
- Don't push to `main` directly

## Reference Docs

For deeper context, read these files as needed:
- `memory/MEMORY.md` — full project history and operating principles
- `memory/WORKFLOW.md` — detailed git workflow steps
- `memory/CLAUDE.md` — legacy Claude-specific notes
- `README.md` — user-facing setup and usage docs