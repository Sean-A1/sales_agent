"""FastAPI 앱 — Sales Agent HTTP 인터페이스."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db import create_tables

from .routes import cart, chat, orders, products


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 DB 테이블 생성."""
    await create_tables()
    yield


app = FastAPI(title="Sales Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, tags=["chat"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(cart.router, prefix="/cart", tags=["cart"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
