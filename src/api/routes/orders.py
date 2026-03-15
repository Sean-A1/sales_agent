"""주문 엔드포인트 — 생성, 조회."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import create_order, get_order, get_orders, get_session
from src.models import OrderCreate, OrderRead

router = APIRouter()


@router.post("", response_model=OrderRead)
async def place_order(
    data: OrderCreate,
    session: AsyncSession = Depends(get_session),
):
    """주문을 생성한다."""
    return await create_order(session, data)


@router.get("/{order_id}", response_model=OrderRead)
async def read_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
):
    """주문을 조회한다."""
    order = await get_order(session, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다")
    return order


@router.get("/user/{user_id}", response_model=list[OrderRead])
async def list_user_orders(
    user_id: str,
    session: AsyncSession = Depends(get_session),
):
    """사용자의 주문 목록을 조회한다."""
    return await get_orders(session, user_id)
