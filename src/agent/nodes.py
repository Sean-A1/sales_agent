"""Agent node functions for each intent."""

import json

from openai import AsyncOpenAI
from sqlmodel import select

from src.core import get_logger
from src.db import get_engine, get_session
from src.graph import (
    get_driver,
    execute_query,
    get_related_products,
    get_session_context,
)
from src.models import Product, CartItem, Order, OrderItem
from src.rag import get_qdrant_client, get_embedder, search_reviews, search_qna

from .state import AgentState

from src.core import get_logger, get_settings

logger = get_logger(__name__)


async def search_node(state: AgentState) -> AgentState:
    """Search products by keyword from context query or last user message."""
    query = state.get("context", {}).get("query") or _last_user_message(state)
    engine = get_engine()
    async for session in get_session(engine):
        stmt = (
            select(Product)
            .where(Product.name.contains(query) | Product.category.contains(query))
            .limit(10)
        )
        result = await session.exec(stmt)
        products = list(result.all())

    items = [
        {
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "price": p.price,
            "stock": p.stock,
        }
        for p in products
    ]
    return {**state, "result": {"type": "search", "products": items}}


async def recommend_node(state: AgentState) -> AgentState:
    """Recommend products via Neo4j relationships."""
    context = state.get("context", {})
    category = context.get("category", "")

    driver = get_driver()
    try:
        if category:
            query = """
            MATCH (p:Product {category: $category})
            RETURN p {.product_id, .name, .category, .brand, .price} AS product
            LIMIT $limit
            """
            records = await execute_query(
                driver, query, {"category": category, "limit": 5}
            )
        else:
            query = """
            MATCH (p:Product)
            RETURN p {.product_id, .name, .category, .brand, .price} AS product
            LIMIT $limit
            """
            records = await execute_query(driver, query, {"limit": 5})

        products = [r["product"] for r in records]
    finally:
        await driver.close()

    return {**state, "result": {"type": "recommend", "products": products}}


async def detail_node(state: AgentState) -> AgentState:
    """Get product detail by ID extracted from context."""
    product_id = state.get("context", {}).get("product_id")
    if not product_id:
        return {
            **state,
            "result": {"type": "detail", "error": "상품 ID를 찾을 수 없습니다."},
        }

    engine = get_engine()
    async for session in get_session(engine):
        product = await session.get(Product, int(product_id))

    if not product:
        return {
            **state,
            "result": {"type": "detail", "error": "상품을 찾을 수 없습니다."},
        }

    return {
        **state,
        "result": {
            "type": "detail",
            "product": {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "category": product.category,
                "brand": product.brand,
                "price": product.price,
                "stock": product.stock,
                "specs": product.specs,
            },
        },
    }


async def stock_node(state: AgentState) -> AgentState:
    """Check stock and price for a product."""
    product_id = state.get("context", {}).get("product_id")
    if not product_id:
        return {
            **state,
            "result": {"type": "stock", "error": "상품 ID를 찾을 수 없습니다."},
        }

    engine = get_engine()
    async for session in get_session(engine):
        product = await session.get(Product, int(product_id))

    if not product:
        return {
            **state,
            "result": {"type": "stock", "error": "상품을 찾을 수 없습니다."},
        }

    return {
        **state,
        "result": {
            "type": "stock",
            "product_id": product.id,
            "name": product.name,
            "price": product.price,
            "stock": product.stock,
            "in_stock": product.stock > 0,
        },
    }


async def review_node(state: AgentState) -> AgentState:
    """Search reviews via Qdrant RAG."""
    query = _last_user_message(state)
    product_id = state.get("context", {}).get("product_id")

    client = get_qdrant_client()
    embedder = get_embedder()

    reviews = search_reviews(
        client,
        embedder,
        query,
        product_id=int(product_id) if product_id else None,
        limit=5,
    )
    qna = search_qna(
        client,
        embedder,
        query,
        product_id=int(product_id) if product_id else None,
        limit=3,
    )

    return {
        **state,
        "result": {"type": "review", "reviews": reviews, "qna": qna},
    }


async def cart_node(state: AgentState) -> AgentState:
    """Manage cart: add item or list cart."""
    session_id = state["session_id"]
    context = state.get("context", {})
    product_id = context.get("product_id")
    quantity = context.get("quantity", 1)

    engine = get_engine()
    if product_id:
        async for session in get_session(engine):
            item = CartItem(
                session_id=session_id,
                product_id=int(product_id),
                quantity=int(quantity),
            )
            session.add(item)
            await session.commit()
            await session.refresh(item)
        return {
            **state,
            "result": {
                "type": "cart",
                "action": "added",
                "product_id": int(product_id),
                "quantity": int(quantity),
            },
        }

    async for session in get_session(engine):
        stmt = select(CartItem).where(CartItem.session_id == session_id)
        result = await session.exec(stmt)
        items = list(result.all())

    cart = [{"product_id": i.product_id, "quantity": i.quantity} for i in items]
    return {**state, "result": {"type": "cart", "action": "list", "items": cart}}


async def order_track_node(state: AgentState) -> AgentState:
    """Track order status."""
    order_id = state.get("context", {}).get("order_id")
    if not order_id:
        return {
            **state,
            "result": {"type": "order_track", "error": "주문 ID를 찾을 수 없습니다."},
        }

    engine = get_engine()
    async for session in get_session(engine):
        order = await session.get(Order, int(order_id))

    if not order:
        return {
            **state,
            "result": {"type": "order_track", "error": "주문을 찾을 수 없습니다."},
        }

    return {
        **state,
        "result": {
            "type": "order_track",
            "order_id": order.id,
            "status": order.status,
            "total_price": order.total_price,
            "created_at": order.created_at.isoformat(),
        },
    }


async def unknown_node(state: AgentState) -> AgentState:
    """Handle unknown intents."""
    return {
        **state,
        "result": {
            "type": "unknown",
            "message": "죄송합니다, 요청을 이해하지 못했습니다. "
            "상품 검색, 추천, 재고 확인 등을 도와드릴 수 있습니다.",
        },
    }


_RESPONSE_SYSTEM_PROMPT = """\
당신은 신세계 라이브 홈쇼핑의 AI 판매 상담사입니다.
고객에게 친절하고 전문적인 톤으로 자연스러운 한국어 응답을 생성하세요.

규칙:
- 상품 추천/검색 결과: 상품명, 가격, 주요 특징을 간결하게 안내
- 리뷰 관련: 리뷰 내용을 요약하여 전달
- 재고/가격 확인: 재고 상태와 가격을 명확하게 안내
- 주문 추적: 주문 상태를 명확하게 안내
- 장바구니: 추가/목록 결과를 안내
- 항상 존댓말 사용
- 불필요하게 길지 않게, 핵심 정보 중심으로 답변
"""


async def response_node(state: AgentState) -> AgentState:
    """Generate a natural language response from intent node result."""
    result = state.get("result", {})
    messages = state.get("messages", [])
    user_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
        if m["role"] in ("user", "assistant")
    ]
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _RESPONSE_SYSTEM_PROMPT},
            *user_messages,
            {
                "role": "system",
                "content": f"아래는 시스템 조회 결과입니다. 이 데이터를 바탕으로 고객에게 응답하세요.\n\n{json.dumps(result, ensure_ascii=False, default=str)}",
            },
        ],
        temperature=0.7,
        max_tokens=1024,
    )
    answer = response.choices[0].message.content
    updated_result = {**result, "answer": answer}
    return {**state, "result": updated_result}


def _last_user_message(state: AgentState) -> str:
    """Extract the last user message content."""
    for msg in reversed(state["messages"]):
        if msg["role"] == "user":
            return msg["content"]
    return ""
