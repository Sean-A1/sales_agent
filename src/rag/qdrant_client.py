"""Qdrant 클라이언트 — 벡터 DB 연결 및 컬렉션 관리."""

from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from src.core.config import get_settings


def get_qdrant_client() -> QdrantClient:
    """QDRANT_URL, QDRANT_API_KEY 기반 QdrantClient를 반환한다."""
    settings = get_settings()
    return QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY or None,
    )


def ensure_collection(
    client: QdrantClient,
    collection_name: str,
    vector_size: int = 1536,
) -> None:
    """컬렉션이 없으면 cosine distance로 생성한다."""
    existing = [c.name for c in client.get_collections().collections]
    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )
