"""장바구니(Cart) 도메인 모델."""

from datetime import UTC, datetime

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class CartItem(SQLModel, table=True):
    """장바구니 아이템 테이블."""

    __tablename__ = "cart_items"

    id: int | None = Field(default=None, primary_key=True)
    session_id: str = Field(max_length=200, index=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    quantity: int = Field(ge=1, default=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CartItemCreate(BaseModel):
    """장바구니 아이템 생성 스키마."""

    session_id: str
    product_id: int
    quantity: int = 1


class CartItemRead(BaseModel):
    """장바구니 아이템 조회 스키마."""

    model_config = {"from_attributes": True}

    id: int
    session_id: str
    product_id: int
    quantity: int
    created_at: datetime
