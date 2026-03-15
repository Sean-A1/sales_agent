"""Cart CRUD 함수."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.models import CartItem, CartItemCreate


async def add_to_cart(session: AsyncSession, data: CartItemCreate) -> CartItem:
    """장바구니에 아이템을 추가한다."""
    item = CartItem(**data.model_dump())
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def get_cart(session: AsyncSession, session_id: str) -> list[CartItem]:
    """세션 ID로 장바구니를 조회한다."""
    stmt = select(CartItem).where(CartItem.session_id == session_id)
    result = await session.exec(stmt)
    return list(result.all())


async def remove_from_cart(session: AsyncSession, cart_item_id: int) -> bool:
    """장바구니 아이템을 삭제한다. 성공 시 True."""
    item = await session.get(CartItem, cart_item_id)
    if item is None:
        return False
    await session.delete(item)
    await session.commit()
    return True


async def clear_cart(session: AsyncSession, session_id: str) -> int:
    """세션의 장바구니를 비운다. 삭제된 아이템 수를 반환한다."""
    items = await get_cart(session, session_id)
    count = len(items)
    for item in items:
        await session.delete(item)
    await session.commit()
    return count
