"""DB 레이어 테스트 — in-memory SQLite (Docker 불필요)."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db import (
    add_to_cart,
    clear_cart,
    create_order,
    create_product,
    create_tables,
    get_cart,
    get_order,
    get_orders,
    get_product,
    get_products,
    remove_from_cart,
    update_order_status,
    update_stock,
)
from src.models import (
    CartItemCreate,
    OrderCreate,
    OrderItemCreate,
    OrderStatus,
    ProductCreate,
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


# ── Product CRUD ────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_get_product(session):
    data = ProductCreate(
        name="삼성 갤럭시 S25",
        category="스마트폰",
        brand="삼성",
        price=1_350_000,
        stock=50,
    )
    product = await create_product(session, data)
    assert product.id is not None
    assert product.name == "삼성 갤럭시 S25"

    fetched = await get_product(session, product.id)
    assert fetched is not None
    assert fetched.price == 1_350_000


@pytest.mark.asyncio
async def test_get_product_not_found(session):
    assert await get_product(session, 9999) is None


@pytest.mark.asyncio
async def test_get_products_with_category(session):
    for i in range(3):
        await create_product(
            session,
            ProductCreate(name=f"폰{i}", category="스마트폰", price=100_000),
        )
    await create_product(
        session, ProductCreate(name="TV", category="가전", price=500_000)
    )

    phones = await get_products(session, category="스마트폰")
    assert len(phones) == 3

    all_products = await get_products(session)
    assert len(all_products) == 4


@pytest.mark.asyncio
async def test_get_products_pagination(session):
    for i in range(5):
        await create_product(
            session,
            ProductCreate(name=f"상품{i}", category="기타", price=10_000),
        )
    page = await get_products(session, skip=2, limit=2)
    assert len(page) == 2


@pytest.mark.asyncio
async def test_update_stock(session):
    product = await create_product(
        session,
        ProductCreate(name="재고 테스트", category="기타", price=10_000, stock=10),
    )
    updated = await update_stock(session, product.id, -3)
    assert updated is not None
    assert updated.stock == 7

    updated = await update_stock(session, product.id, 5)
    assert updated.stock == 12


@pytest.mark.asyncio
async def test_update_stock_insufficient(session):
    product = await create_product(
        session,
        ProductCreate(name="부족 테스트", category="기타", price=10_000, stock=2),
    )
    with pytest.raises(ValueError, match="재고 부족"):
        await update_stock(session, product.id, -5)


@pytest.mark.asyncio
async def test_update_stock_not_found(session):
    assert await update_stock(session, 9999, 1) is None


# ── Cart CRUD ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_and_get_cart(session):
    # 상품 먼저 생성
    product = await create_product(
        session,
        ProductCreate(name="장바구니용", category="기타", price=5_000, stock=10),
    )
    item = await add_to_cart(
        session,
        CartItemCreate(session_id="sess_1", product_id=product.id, quantity=2),
    )
    assert item.id is not None
    assert item.quantity == 2

    cart = await get_cart(session, "sess_1")
    assert len(cart) == 1
    assert cart[0].product_id == product.id


@pytest.mark.asyncio
async def test_remove_from_cart(session):
    product = await create_product(
        session,
        ProductCreate(name="삭제용", category="기타", price=1_000, stock=5),
    )
    item = await add_to_cart(
        session,
        CartItemCreate(session_id="sess_2", product_id=product.id),
    )
    assert await remove_from_cart(session, item.id) is True
    assert await remove_from_cart(session, item.id) is False

    cart = await get_cart(session, "sess_2")
    assert len(cart) == 0


@pytest.mark.asyncio
async def test_clear_cart(session):
    product = await create_product(
        session,
        ProductCreate(name="클리어용", category="기타", price=2_000, stock=10),
    )
    for _ in range(3):
        await add_to_cart(
            session,
            CartItemCreate(session_id="sess_3", product_id=product.id),
        )
    deleted = await clear_cart(session, "sess_3")
    assert deleted == 3

    cart = await get_cart(session, "sess_3")
    assert len(cart) == 0


# ── Order CRUD ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_get_order(session):
    # 상품 생성
    p1 = await create_product(
        session,
        ProductCreate(name="주문상품1", category="기타", price=10_000, stock=10),
    )
    p2 = await create_product(
        session,
        ProductCreate(name="주문상품2", category="기타", price=20_000, stock=5),
    )

    data = OrderCreate(
        user_id="user_001",
        items=[
            OrderItemCreate(product_id=p1.id, quantity=2, unit_price=10_000),
            OrderItemCreate(product_id=p2.id, quantity=1, unit_price=20_000),
        ],
    )
    order = await create_order(session, data)
    assert order.id is not None
    assert order.total_price == 40_000
    assert order.status == OrderStatus.PENDING

    fetched = await get_order(session, order.id)
    assert fetched is not None
    assert fetched.user_id == "user_001"


@pytest.mark.asyncio
async def test_get_order_not_found(session):
    assert await get_order(session, 9999) is None


@pytest.mark.asyncio
async def test_get_orders_by_user(session):
    p = await create_product(
        session,
        ProductCreate(name="유저 주문", category="기타", price=5_000, stock=20),
    )
    for _ in range(2):
        await create_order(
            session,
            OrderCreate(
                user_id="user_002",
                items=[OrderItemCreate(product_id=p.id, quantity=1, unit_price=5_000)],
            ),
        )
    await create_order(
        session,
        OrderCreate(
            user_id="user_003",
            items=[OrderItemCreate(product_id=p.id, quantity=1, unit_price=5_000)],
        ),
    )

    orders = await get_orders(session, "user_002")
    assert len(orders) == 2

    orders = await get_orders(session, "user_003")
    assert len(orders) == 1


@pytest.mark.asyncio
async def test_update_order_status(session):
    p = await create_product(
        session,
        ProductCreate(name="상태변경", category="기타", price=3_000, stock=10),
    )
    order = await create_order(
        session,
        OrderCreate(
            user_id="user_004",
            items=[OrderItemCreate(product_id=p.id, quantity=1, unit_price=3_000)],
        ),
    )
    updated = await update_order_status(session, order.id, OrderStatus.CONFIRMED)
    assert updated is not None
    assert updated.status == OrderStatus.CONFIRMED

    updated = await update_order_status(session, order.id, OrderStatus.DELIVERED)
    assert updated.status == OrderStatus.DELIVERED


@pytest.mark.asyncio
async def test_update_order_status_not_found(session):
    assert await update_order_status(session, 9999, OrderStatus.CONFIRMED) is None
