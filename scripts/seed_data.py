"""신세계 라이브 홈쇼핑 더미 데이터 생성 및 적재 스크립트.

Usage:
    poetry run python scripts/seed_data.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from loguru import logger
from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core import get_logger, get_settings
from src.db import create_product, create_tables, get_engine, get_products
from src.graph import (
    close_driver,
    create_category_relationship,
    create_product_node,
    get_driver,
)
from src.models import Product, ProductCreate, Review, ReviewCreate
from src.rag import get_embedder, get_qdrant_client, ingest_qna, ingest_reviews

log = get_logger("seed_data")

# ---------------------------------------------------------------------------
# 카테고리 정의
# ---------------------------------------------------------------------------
CATEGORIES = [
    "패션/의류",
    "뷰티/화장품",
    "가전/디지털",
    "식품/건강",
    "생활/주방",
]

PRODUCTS_PER_CATEGORY = 6
REVIEWS_PER_PRODUCT = 10
QNA_PER_PRODUCT = 5


# ---------------------------------------------------------------------------
# OpenAI GPT로 더미 데이터 생성
# ---------------------------------------------------------------------------

def _build_product_prompt(category: str) -> str:
    return f"""신세계 라이브 홈쇼핑에서 판매할 법한 '{category}' 카테고리 상품 {PRODUCTS_PER_CATEGORY}개를 JSON 배열로 생성해주세요.

각 상품은 다음 필드를 포함합니다:
- name: 상품명 (한국어, 브랜드명 포함)
- description: 상세 설명 (2~3문장, 홈쇼핑 방송 느낌)
- brand: 브랜드명
- price: 가격 (원, 정수)
- stock: 재고 수량 (50~500 사이)
- specs: 상품 스펙 (JSON 객체, 카테고리에 맞는 3~5개 항목)

홈쇼핑 특가 느낌으로 가격을 설정하고, 실제 존재하는 브랜드와 비슷한 느낌의 이름을 사용하세요.
JSON 배열만 반환하세요. 마크다운 코드블록 없이 순수 JSON만."""


def _build_review_prompt(product_name: str) -> str:
    return f"""'{product_name}' 상품에 대한 홈쇼핑 구매 리뷰 {REVIEWS_PER_PRODUCT}개를 JSON 배열로 생성해주세요.

각 리뷰:
- rating: 별점 (1~5, 4~5점 비중 높게)
- content: 리뷰 내용 (1~3문장, 자연스러운 한국어 구어체)
- author: 작성자 닉네임 (한국어)

실제 홈쇼핑 리뷰처럼 배송, 가격, 품질 등을 언급하세요.
JSON 배열만 반환하세요. 마크다운 코드블록 없이 순수 JSON만."""


def _build_qna_prompt(product_name: str) -> str:
    return f"""'{product_name}' 상품에 대한 Q&A {QNA_PER_PRODUCT}개를 JSON 배열로 생성해주세요.

각 Q&A:
- question: 고객 질문 (한국어, 실제 홈쇼핑에서 자주 하는 질문)
- answer: 판매자 답변 (한국어, 친절한 톤)

배송, 교환/반품, 사이즈, 사용법, 호환성 등 다양한 주제를 다루세요.
JSON 배열만 반환하세요. 마크다운 코드블록 없이 순수 JSON만."""


def _call_gpt(client: OpenAI, prompt: str) -> list[dict]:
    """GPT를 호출하여 JSON 배열을 파싱한다."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content.strip()
    parsed = json.loads(raw)
    # json_object 모드는 최상위가 object이므로 배열을 추출
    if isinstance(parsed, dict):
        for v in parsed.values():
            if isinstance(v, list):
                return v
    return parsed


def generate_products(client: OpenAI) -> list[dict]:
    """카테고리별 상품 데이터를 생성한다."""
    all_products: list[dict] = []
    for cat in CATEGORIES:
        log.info(f"상품 생성 중: {cat}")
        products = _call_gpt(client, _build_product_prompt(cat))
        for p in products:
            p["category"] = cat
        all_products.extend(products)
    log.info(f"총 {len(all_products)}개 상품 생성 완료")
    return all_products


def generate_reviews(client: OpenAI, products: list[dict]) -> list[dict]:
    """상품별 리뷰 데이터를 생성한다."""
    all_reviews: list[dict] = []
    for i, p in enumerate(products):
        log.info(f"리뷰 생성 중: [{i+1}/{len(products)}] {p['name']}")
        reviews = _call_gpt(client, _build_review_prompt(p["name"]))
        for r in reviews:
            r["_product_index"] = i
        all_reviews.extend(reviews)
    log.info(f"총 {len(all_reviews)}개 리뷰 생성 완료")
    return all_reviews


def generate_qna(client: OpenAI, products: list[dict]) -> list[dict]:
    """상품별 Q&A 데이터를 생성한다."""
    all_qna: list[dict] = []
    for i, p in enumerate(products):
        log.info(f"Q&A 생성 중: [{i+1}/{len(products)}] {p['name']}")
        qna = _call_gpt(client, _build_qna_prompt(p["name"]))
        for q in qna:
            q["_product_index"] = i
        all_qna.extend(qna)
    log.info(f"총 {len(all_qna)}개 Q&A 생성 완료")
    return all_qna


# ---------------------------------------------------------------------------
# PostgreSQL 적재
# ---------------------------------------------------------------------------

async def seed_postgres(
    products_data: list[dict],
    reviews_data: list[dict],
) -> list[Product]:
    """PostgreSQL에 상품 및 리뷰를 적재한다."""
    engine = get_engine()
    await create_tables(engine)

    async with SQLModelAsyncSession(engine, expire_on_commit=False) as session:
        # 이미 데이터가 있으면 스킵
        existing = await get_products(session, limit=1)
        if existing:
            log.info("PostgreSQL: 이미 상품 데이터가 존재합니다. 스킵.")
            # 기존 상품 전체 조회
            all_products = await get_products(session, limit=100)
            await engine.dispose()
            return all_products

        # 상품 적재
        created_products: list[Product] = []
        for pd in products_data:
            product = await create_product(
                session,
                ProductCreate(
                    name=pd["name"],
                    description=pd.get("description", ""),
                    category=pd["category"],
                    brand=pd.get("brand", ""),
                    price=pd["price"],
                    stock=pd.get("stock", 100),
                    specs=pd.get("specs"),
                ),
            )
            created_products.append(product)
        await session.commit()
        log.info(f"PostgreSQL: {len(created_products)}개 상품 적재 완료")

        # 리뷰 적재
        review_count = 0
        for rd in reviews_data:
            idx = rd["_product_index"]
            product_id = created_products[idx].id
            review = Review(
                product_id=product_id,
                rating=rd.get("rating", 5),
                content=rd.get("content", ""),
                author=rd.get("author", "익명"),
            )
            session.add(review)
            review_count += 1
        await session.commit()
        log.info(f"PostgreSQL: {review_count}개 리뷰 적재 완료")

    await engine.dispose()
    return created_products


# ---------------------------------------------------------------------------
# Neo4j 적재
# ---------------------------------------------------------------------------

async def seed_neo4j(products: list[Product]) -> None:
    """Neo4j에 상품 노드 및 카테고리 관계를 생성한다."""
    driver = get_driver()
    try:
        # 이미 데이터가 있는지 확인
        from src.graph import execute_query

        result = await execute_query(
            driver, "MATCH (p:Product) RETURN count(p) AS cnt"
        )
        if result and result[0].get("cnt", 0) > 0:
            log.info("Neo4j: 이미 상품 노드가 존재합니다. 스킵.")
            return

        for p in products:
            await create_product_node(
                driver,
                product_id=p.id,
                name=p.name,
                category=p.category,
                brand=p.brand,
                price=p.price,
                specs=p.specs,
            )
            await create_category_relationship(driver, p.id, p.category)
        log.info(f"Neo4j: {len(products)}개 상품 노드 및 카테고리 관계 생성 완료")
    finally:
        await close_driver(driver)


# ---------------------------------------------------------------------------
# Qdrant 적재
# ---------------------------------------------------------------------------

def seed_qdrant(
    products: list[Product],
    reviews_data: list[dict],
    qna_data: list[dict],
) -> None:
    """Qdrant에 리뷰 및 Q&A 임베딩을 적재한다."""
    client = get_qdrant_client()
    embedder = get_embedder()

    # 이미 데이터가 있는지 확인
    from src.rag import COLLECTION_NAME

    try:
        info = client.get_collection(COLLECTION_NAME)
        if info.points_count and info.points_count > 0:
            log.info("Qdrant: 이미 임베딩 데이터가 존재합니다. 스킵.")
            return
    except Exception:
        pass  # 컬렉션이 없으면 계속 진행

    # product_index → product_id 매핑
    id_map = {i: p.id for i, p in enumerate(products)}

    # 리뷰 임베딩
    review_dicts = [
        {
            "product_id": id_map[r["_product_index"]],
            "content": r.get("content", ""),
            "author": r.get("author", ""),
            "rating": r.get("rating", 5),
        }
        for r in reviews_data
    ]
    review_count = ingest_reviews(client, embedder, review_dicts)
    log.info(f"Qdrant: {review_count}개 리뷰 임베딩 적재 완료")

    # Q&A 임베딩
    qna_dicts = [
        {
            "product_id": id_map[q["_product_index"]],
            "question": q.get("question", ""),
            "answer": q.get("answer", ""),
        }
        for q in qna_data
    ]
    qna_count = ingest_qna(client, embedder, qna_dicts)
    log.info(f"Qdrant: {qna_count}개 Q&A 임베딩 적재 완료")


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------

async def main() -> None:
    log.info("=== 신세계 라이브 홈쇼핑 시드 데이터 생성 시작 ===")

    settings = get_settings()
    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # 1. GPT로 더미 데이터 생성
    log.info("--- 1단계: GPT 더미 데이터 생성 ---")
    products_data = generate_products(openai_client)
    reviews_data = generate_reviews(openai_client, products_data)
    qna_data = generate_qna(openai_client, products_data)

    # 2. PostgreSQL 적재
    log.info("--- 2단계: PostgreSQL 적재 ---")
    products = await seed_postgres(products_data, reviews_data)

    # 3. Neo4j 적재
    log.info("--- 3단계: Neo4j 적재 ---")
    await seed_neo4j(products)

    # 4. Qdrant 적재
    log.info("--- 4단계: Qdrant 적재 ---")
    seed_qdrant(products, reviews_data, qna_data)

    log.info("=== 시드 데이터 적재 완료 ===")


if __name__ == "__main__":
    asyncio.run(main())
