# B2C General Sales Agent

AI 기반 범용 판매 에이전트. 고객과의 자연어 대화를 통해 상품 검색, 추천, 주문까지 원스톱으로 처리합니다.

## Stack

- **Agent**: LangGraph (멀티스텝 에이전트 오케스트레이션)
- **Knowledge Graph**: Neo4j (상품 관계, 카테고리 탐색)
- **Vector Store**: Qdrant (상품 설명·리뷰 RAG)
- **Database**: PostgreSQL + SQLModel (주문, 재고, 사용자)
- **API**: FastAPI
- **LLM**: OpenAI

## Features

| 기능 | 설명 |
|---|---|
| 상품 검색 | 키워드·카테고리·필터 기반 검색 |
| 상품 추천 | 선호도·구매 이력 기반 개인화 추천 |
| 상품 상세 | 스펙 비교, 상세 정보 응답 |
| 대화 맥락 유지 | 멀티턴 컨텍스트 관리 |
| 재고/가격 확인 | 실시간 재고·가격 조회 |
| 리뷰 기반 응답 | 사용자 리뷰 RAG 검색 |
| 장바구니/주문 | 장바구니 추가, 주문 생성 |
| 주문 추적 | 주문 상태 조회 |

## Quick Start

### 1. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env
# 필요한 키 설정: OPENAI_API_KEY, DATABASE_URL 등
```

### 2. 인프라 실행

```bash
docker compose up -d
```

### 3. 의존성 설치

```bash
poetry install
```

### 4. 서버 실행

```bash
poetry run uvicorn src.api.main:app --reload
```

### 5. 테스트

```bash
poetry run pytest tests/ -v
```

## Development

```bash
# 새 브랜치에서 작업
git checkout -b sean/<task-name>

# 또는 Claude 에이전트 브랜치
git checkout -b claude/<task-name>
```

`main` 브랜치에 직접 커밋하지 않습니다. PR을 통해 머지합니다.
