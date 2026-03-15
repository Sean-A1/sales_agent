"""장바구니 엔드포인트 — 추가, 조회, 삭제."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import add_to_cart, get_cart, get_session, remove_from_cart
from src.models import CartItemCreate, CartItemRead

router = APIRouter()


@router.post("", response_model=CartItemRead)
async def create_cart_item(
    data: CartItemCreate,
    session: AsyncSession = Depends(get_session),
):
    """장바구니에 상품을 추가한다."""
    return await add_to_cart(session, data)


@router.get("/{session_id}", response_model=list[CartItemRead])
async def read_cart(
    session_id: str,
    session: AsyncSession = Depends(get_session),
):
    """세션의 장바구니를 조회한다."""
    return await get_cart(session, session_id)


@router.delete("/{cart_item_id}")
async def delete_cart_item(
    cart_item_id: int,
    session: AsyncSession = Depends(get_session),
):
    """장바구니 아이템을 삭제한다."""
    removed = await remove_from_cart(session, cart_item_id)
    if not removed:
        raise HTTPException(status_code=404, detail="장바구니 아이템을 찾을 수 없습니다")
    return {"ok": True}
