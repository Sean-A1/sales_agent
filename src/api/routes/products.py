"""상품 엔드포인트 — 목록 조회, 상세 조회."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_product, get_products, get_session
from src.models import ProductRead

router = APIRouter()


@router.get("", response_model=list[ProductRead])
async def list_products(
    category: str | None = None,
    skip: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
):
    """상품 목록을 조회한다."""
    return await get_products(session, category=category, skip=skip, limit=limit)


@router.get("/{product_id}", response_model=ProductRead)
async def read_product(
    product_id: int,
    session: AsyncSession = Depends(get_session),
):
    """상품 상세를 조회한다."""
    product = await get_product(session, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    return product
