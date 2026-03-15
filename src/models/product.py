"""상품(Product) 도메인 모델."""

from datetime import UTC, datetime

from pydantic import BaseModel
from sqlmodel import JSON, Column, Field, SQLModel


class Product(SQLModel, table=True):
    """상품 테이블."""

    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=200, index=True)
    description: str = Field(default="")
    category: str = Field(max_length=100, index=True)
    brand: str = Field(default="", max_length=100)
    price: int = Field(ge=0, description="가격 (원)")
    stock: int = Field(default=0, ge=0)
    image_url: str = Field(default="")
    specs: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProductCreate(BaseModel):
    """상품 생성 스키마."""

    name: str
    description: str = ""
    category: str
    brand: str = ""
    price: int
    stock: int = 0
    image_url: str = ""
    specs: dict | None = None


class ProductRead(BaseModel):
    """상품 조회 스키마."""

    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str
    category: str
    brand: str
    price: int
    stock: int
    image_url: str
    specs: dict | None
    created_at: datetime
    updated_at: datetime
