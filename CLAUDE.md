# CLAUDE.md

## Project

B2C General Sales Agent — AI 기반 범용 판매 에이전트.
고객 대화를 통해 상품 검색/추천, 재고·가격 확인, 주문 연동까지 처리.

## Stack

| Layer | Technology |
|---|---|
| Agent Orchestration | LangGraph |
| Knowledge Graph | Neo4j |
| Vector Store | Qdrant |
| Database | PostgreSQL (SQLModel) |
| API | FastAPI |
| LLM | OpenAI |

## Features

- 상품 검색 (키워드, 카테고리, 필터)
- 상품 추천 (사용자 선호도, 구매 이력 기반)
- 상품 상세 응답 (스펙, 비교)
- 대화 맥락 유지 (멀티턴 컨텍스트)
- 재고/가격 확인 (실시간 조회)
- 리뷰 기반 응답 (RAG)
- 장바구니/주문 연동
- 주문 추적

## Repo Map

```
main.py                  # entrypoint
src/
  agent/                 # LangGraph agent nodes & tools
  api/                   # FastAPI routes
  graph/                 # LangGraph graph definitions & state
  rag/                   # Qdrant RAG pipeline
  db/                    # PostgreSQL & Neo4j connections
  models/                # SQLModel & Pydantic schemas
  core/                  # config, logging, shared utilities
tests/                   # pytest test suites
docker-compose.yml       # PostgreSQL, Qdrant
```

## Commands

```bash
# Run API server
poetry run uvicorn src.api.main:app --reload

# Test
poetry run pytest tests/ -v

# Lint check
poetry run python -c "import src; print('import ok')"
```

## Branch Policy

NEVER work directly on `main`. Always:
1. `git checkout main && git pull`
2. `git checkout -b sean/<task>` or `git checkout -b claude/<task>`
3. Work → commit → review diff
4. Merge to main via PR

## Key Rules

- **Minimal edits only.** Small, focused changes. No broad refactors unless explicitly requested.
- **No secrets in commits.** Never commit `.env`, tokens, or credentials.
- **Poetry.** Always use `poetry run` prefix. Python 3.11+.
- **Korean context.** 사용자 인터페이스와 상품 데이터는 한국어 기반.

## Validation Before Commit

1. Import check: `poetry run python -c "import src"`
2. Targeted test: `poetry run pytest tests/<target> -v`
3. Full suite: `poetry run pytest tests/ -v`
4. Review diff: `git diff --stat`

## What NOT to Do

- Don't introduce unrelated dependency churn
- Don't make formatting-only changes unless requested
- Don't modify `.env` policy without explicit instruction
- Don't push to `main` directly
