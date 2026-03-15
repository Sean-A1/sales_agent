"""리뷰(Review) 도메인 모델."""

from datetime import UTC, datetime

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class Review(SQLModel, table=True):
    """리뷰 테이블."""

    __tablename__ = "reviews"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    rating: int = Field(ge=1, le=5)
    content: str = Field(default="")
    author: str = Field(max_length=100)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReviewCreate(BaseModel):
    """리뷰 생성 스키마."""

    product_id: int
    rating: int = Field(ge=1, le=5)
    content: str = ""
    author: str


class ReviewRead(BaseModel):
    """리뷰 조회 스키마."""

    model_config = {"from_attributes": True}

    id: int
    product_id: int
    rating: int
    content: str
    author: str
    created_at: datetime
