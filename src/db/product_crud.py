"""Product CRUD 함수."""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.models import Product, ProductCreate


async def create_product(session: AsyncSession, data: ProductCreate) -> Product:
    """상품을 생성한다."""
    product = Product(**data.model_dump())
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def get_product(session: AsyncSession, product_id: int) -> Product | None:
    """ID로 상품을 조회한다."""
    return await session.get(Product, product_id)


async def get_products(
    session: AsyncSession,
    category: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Product]:
    """상품 목록을 조회한다. category 필터 지원."""
    stmt = select(Product)
    if category:
        stmt = stmt.where(Product.category == category)
    stmt = stmt.offset(skip).limit(limit)
    result = await session.exec(stmt)
    return list(result.all())


async def update_stock(
    session: AsyncSession, product_id: int, delta: int
) -> Product | None:
    """재고를 delta만큼 변경한다 (양수: 입고, 음수: 출고)."""
    product = await session.get(Product, product_id)
    if product is None:
        return None
    new_stock = product.stock + delta
    if new_stock < 0:
        raise ValueError(f"재고 부족: 현재 {product.stock}, 요청 {delta}")
    product.stock = new_stock
    product.updated_at = datetime.now(UTC)
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product
