"""API 레이어 테스트 — FastAPI TestClient + in-memory SQLite."""

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.main import app
from src.db import get_session
from src.db.postgres import create_tables
from src.models import (
    CartItemCreate,
    OrderCreate,
    OrderItemCreate,
    ProductCreate,
)
from src.db import (
    add_to_cart,
    create_order,
    create_product,
)

# ── Fixtures ────────────────────────────────────────────


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite://", echo=False)
    await create_tables(eng)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine):
    async with AsyncSession(engine, expire_on_commit=False) as sess:
        yield sess


@pytest_asyncio.fixture
async def client(engine):
    """TestClient with DB session override."""

    async def _override_session():
        async with AsyncSession(engine, expire_on_commit=False) as sess:
            yield sess

    app.dependency_overrides[get_session] = _override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Products ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_products_empty(client):
    resp = await client.get("/products")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_and_list_products(client, session):
    await create_product(
        session,
        ProductCreate(name="갤럭시 S25", category="스마트폰", price=1_350_000, stock=10),
    )
    await create_product(
        session,
        ProductCreate(name="아이폰 16", category="스마트폰", price=1_500_000, stock=5),
    )
    resp = await client.get("/products")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_products_with_category(client, session):
    await create_product(
        session,
        ProductCreate(name="갤럭시 S25", category="스마트폰", price=1_350_000),
    )
    await create_product(
        session,
        ProductCreate(name="LG TV", category="가전", price=2_000_000),
    )
    resp = await client.get("/products", params={"category": "스마트폰"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["category"] == "스마트폰"


@pytest.mark.asyncio
async def test_list_products_pagination(client, session):
    for i in range(5):
        await create_product(
            session,
            ProductCreate(name=f"상품{i}", category="기타", price=10_000),
        )
    resp = await client.get("/products", params={"skip": 2, "limit": 2})
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_product(client, session):
    p = await create_product(
        session,
        ProductCreate(name="테스트 상품", category="기타", price=50_000, stock=3),
    )
    resp = await client.get(f"/products/{p.id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "테스트 상품"


@pytest.mark.asyncio
async def test_get_product_not_found(client):
    resp = await client.get("/products/9999")
    assert resp.status_code == 404


# ── Cart ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_and_get_cart(client, session):
    p = await create_product(
        session,
        ProductCreate(name="장바구니용", category="기타", price=5_000, stock=10),
    )
    resp = await client.post(
        "/cart",
        json={"session_id": "sess_1", "product_id": p.id, "quantity": 2},
    )
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 2

    resp = await client.get("/cart/sess_1")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_delete_cart_item(client, session):
    p = await create_product(
        session,
        ProductCreate(name="삭제용", category="기타", price=1_000, stock=5),
    )
    item = await add_to_cart(
        session,
        CartItemCreate(session_id="sess_2", product_id=p.id, quantity=1),
    )
    resp = await client.delete(f"/cart/{item.id}")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    resp = await client.get("/cart/sess_2")
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_delete_cart_item_not_found(client):
    resp = await client.delete("/cart/9999")
    assert resp.status_code == 404


# ── Orders ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_get_order(client, session):
    p = await create_product(
        session,
        ProductCreate(name="주문상품", category="기타", price=10_000, stock=10),
    )
    resp = await client.post(
        "/orders",
        json={
            "user_id": "user_001",
            "items": [
                {"product_id": p.id, "quantity": 2, "unit_price": 10_000},
            ],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_price"] == 20_000
    assert body["status"] == "pending"

    resp = await client.get(f"/orders/{body['id']}")
    assert resp.status_code == 200
    assert resp.json()["user_id"] == "user_001"


@pytest.mark.asyncio
async def test_get_order_not_found(client):
    resp = await client.get("/orders/9999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_user_orders(client, session):
    p = await create_product(
        session,
        ProductCreate(name="유저주문", category="기타", price=5_000, stock=20),
    )
    for _ in range(2):
        await create_order(
            session,
            OrderCreate(
                user_id="user_002",
                items=[OrderItemCreate(product_id=p.id, quantity=1, unit_price=5_000)],
            ),
        )
    resp = await client.get("/orders/user/user_002")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# ── Chat ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_endpoint(client):
    """채팅 엔드포인트 — 에이전트 그래프를 mock하여 테스트."""
    mock_result = {
        "session_id": "sess_chat",
        "messages": [{"role": "user", "content": "갤럭시 추천해줘"}],
        "intent": "recommend",
        "context": {},
        "result": {"type": "recommend", "products": []},
    }

    mock_graph = AsyncMock()
    mock_graph.ainvoke.return_value = mock_result

    with patch("src.api.routes.chat.build_graph", return_value=mock_graph):
        resp = await client.post(
            "/chat",
            json={"session_id": "sess_chat", "message": "갤럭시 추천해줘"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == "sess_chat"
    assert body["intent"] == "recommend"
    assert body["result"]["type"] == "recommend"


@pytest.mark.asyncio
async def test_chat_unknown_intent(client):
    """분류 불가 인텐트 처리."""
    mock_result = {
        "session_id": "sess_unk",
        "messages": [],
        "intent": "unknown",
        "context": {},
        "result": {"type": "unknown", "message": "죄송합니다"},
    }

    mock_graph = AsyncMock()
    mock_graph.ainvoke.return_value = mock_result

    with patch("src.api.routes.chat.build_graph", return_value=mock_graph):
        resp = await client.post(
            "/chat",
            json={"session_id": "sess_unk", "message": "안녕"},
        )
    assert resp.status_code == 200
    assert resp.json()["intent"] == "unknown"
