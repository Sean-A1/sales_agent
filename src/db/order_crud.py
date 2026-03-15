"""Order CRUD 함수."""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.models import Order, OrderCreate, OrderItem, OrderStatus


async def create_order(session: AsyncSession, data: OrderCreate) -> Order:
    """주문을 생성한다. OrderItem도 함께 생성."""
    total = sum(i.unit_price * i.quantity for i in data.items)
    order = Order(user_id=data.user_id, total_price=total)
    session.add(order)
    await session.flush()  # order.id 확보

    for item_data in data.items:
        order_item = OrderItem(order_id=order.id, **item_data.model_dump())
        session.add(order_item)

    await session.commit()
    await session.refresh(order)
    return order


async def get_order(session: AsyncSession, order_id: int) -> Order | None:
    """ID로 주문을 조회한다."""
    return await session.get(Order, order_id)


async def get_orders(session: AsyncSession, user_id: str) -> list[Order]:
    """사용자 ID로 주문 목록을 조회한다."""
    stmt = select(Order).where(Order.user_id == user_id)
    result = await session.exec(stmt)
    return list(result.all())


async def update_order_status(
    session: AsyncSession, order_id: int, status: OrderStatus
) -> Order | None:
    """주문 상태를 변경한다."""
    order = await session.get(Order, order_id)
    if order is None:
        return None
    order.status = status
    order.updated_at = datetime.now(UTC)
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order
