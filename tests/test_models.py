"""models 레이어 테스트 — 인스턴스 생성 & 스키마 직렬화."""

from datetime import UTC, datetime

from src.models import (
    CartItem,
    CartItemCreate,
    CartItemRead,
    Order,
    OrderCreate,
    OrderItem,
    OrderItemCreate,
    OrderItemRead,
    OrderRead,
    OrderStatus,
    Product,
    ProductCreate,
    ProductRead,
    Review,
    ReviewCreate,
    ReviewRead,
)


# ── Product ──────────────────────────────────────────────


def test_product_instance():
    p = Product(
        id=1,
        name="삼성 갤럭시 S25",
        category="스마트폰",
        brand="삼성",
        price=1_350_000,
        stock=50,
        specs={"color": "블랙", "storage": "256GB"},
    )
    assert p.name == "삼성 갤럭시 S25"
    assert p.price == 1_350_000
    assert p.specs["storage"] == "256GB"


def test_product_create_schema():
    data = ProductCreate(
        name="LG 스탠바이미",
        category="TV",
        price=990_000,
    )
    assert data.name == "LG 스탠바이미"
    assert data.stock == 0


def test_product_read_schema():
    now = datetime.now(UTC)
    p = Product(
        id=1,
        name="테스트 상품",
        category="기타",
        price=10_000,
        created_at=now,
        updated_at=now,
    )
    read = ProductRead.model_validate(p)
    assert read.id == 1
    dumped = read.model_dump()
    assert "name" in dumped


# ── Review ───────────────────────────────────────────────


def test_review_instance():
    r = Review(
        id=1,
        product_id=1,
        rating=5,
        content="배송 빠르고 품질 좋아요!",
        author="홍길동",
    )
    assert r.rating == 5
    assert r.author == "홍길동"


def test_review_create_schema():
    data = ReviewCreate(
        product_id=1,
        rating=4,
        content="괜찮아요",
        author="김철수",
    )
    assert data.rating == 4


def test_review_read_schema():
    r = Review(
        id=1,
        product_id=1,
        rating=3,
        content="보통이에요",
        author="이영희",
    )
    read = ReviewRead.model_validate(r)
    assert read.id == 1
    dumped = read.model_dump()
    assert "author" in dumped


# ── Order ────────────────────────────────────────────────


def test_order_status_enum():
    assert OrderStatus.PENDING == "pending"
    assert OrderStatus.DELIVERED == "delivered"


def test_order_instance():
    o = Order(
        id=1,
        user_id="user_001",
        status=OrderStatus.CONFIRMED,
        total_price=2_500_000,
    )
    assert o.status == OrderStatus.CONFIRMED
    assert o.total_price == 2_500_000


def test_order_item_instance():
    item = OrderItem(
        id=1,
        order_id=1,
        product_id=1,
        quantity=2,
        unit_price=1_250_000,
    )
    assert item.quantity == 2


def test_order_create_schema():
    data = OrderCreate(
        user_id="user_001",
        items=[
            OrderItemCreate(product_id=1, quantity=2, unit_price=1_250_000),
            OrderItemCreate(product_id=3, quantity=1, unit_price=500_000),
        ],
    )
    assert len(data.items) == 2


def test_order_read_schema():
    now = datetime.now(UTC)
    o = Order(
        id=1,
        user_id="user_001",
        total_price=100_000,
        created_at=now,
        updated_at=now,
    )
    read = OrderRead.model_validate(o)
    assert read.status == OrderStatus.PENDING
    dumped = read.model_dump()
    assert "total_price" in dumped


def test_order_item_read_schema():
    item = OrderItem(id=1, order_id=1, product_id=2, quantity=3, unit_price=30_000)
    read = OrderItemRead.model_validate(item)
    assert read.quantity == 3


# ── Cart ─────────────────────────────────────────────────


def test_cart_item_instance():
    c = CartItem(
        id=1,
        session_id="sess_abc123",
        product_id=1,
        quantity=1,
    )
    assert c.session_id == "sess_abc123"


def test_cart_item_create_schema():
    data = CartItemCreate(
        session_id="sess_abc123",
        product_id=5,
        quantity=2,
    )
    assert data.quantity == 2


def test_cart_item_read_schema():
    c = CartItem(
        id=1,
        session_id="sess_abc123",
        product_id=5,
        quantity=2,
    )
    read = CartItemRead.model_validate(c)
    assert read.product_id == 5
    dumped = read.model_dump()
    assert "session_id" in dumped
