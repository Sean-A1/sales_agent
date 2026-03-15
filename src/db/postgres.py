"""PostgreSQL 연결 — async 엔진, 테이블 생성, 세션 의존성."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from src.core.config import get_settings


def get_engine(url: str | None = None):
    """DATABASE_URL 기반 async 엔진을 반환한다."""
    db_url = url or get_settings().DATABASE_URL
    # SQLAlchemy async 드라이버 접두사 변환
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return create_async_engine(db_url, echo=False)


async def create_tables(engine=None) -> None:
    """모든 SQLModel 테이블을 생성한다."""
    eng = engine or get_engine()
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session(engine=None) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Depends 용 AsyncSession 제너레이터."""
    eng = engine or get_engine()
    async with SQLModelAsyncSession(eng, expire_on_commit=False) as session:
        yield session
