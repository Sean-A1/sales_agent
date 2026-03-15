"""주문(Order) 도메인 모델."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class OrderStatus(StrEnum):
    """주문 상태."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPING = "shipping"
    DELIVERED = "delivered"


class Order(SQLModel, table=True):
    """주문 테이블."""

    __tablename__ = "orders"

    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(max_length=100, index=True)
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    total_price: int = Field(ge=0, description="총 금액 (원)")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True)),
    )


class OrderItem(SQLModel, table=True):
    """주문 상품 테이블."""

    __tablename__ = "order_items"

    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    quantity: int = Field(ge=1)
    unit_price: int = Field(ge=0, description="단가 (원)")


class OrderItemCreate(BaseModel):
    """주문 상품 생성 스키마."""

    product_id: int
    quantity: int = Field(ge=1)
    unit_price: int


class OrderCreate(BaseModel):
    """주문 생성 스키마."""

    user_id: str
    items: list[OrderItemCreate]


class OrderItemRead(BaseModel):
    """주문 상품 조회 스키마."""

    model_config = {"from_attributes": True}

    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: int


class OrderRead(BaseModel):
    """주문 조회 스키마."""

    model_config = {"from_attributes": True}

    id: int
    user_id: str
    status: OrderStatus
    total_price: int
    created_at: datetime
    updated_at: datetime
