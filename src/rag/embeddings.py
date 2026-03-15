"""임베딩 유틸리티 — OpenAI text-embedding-3-small 기반."""

from __future__ import annotations

from langchain_openai import OpenAIEmbeddings

from src.core import get_settings


def get_embedder() -> OpenAIEmbeddings:
    settings = get_settings()
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=settings.OPENAI_API_KEY,
    )


def embed_text(embedder: OpenAIEmbeddings, text: str) -> list[float]:
    """단일 텍스트를 임베딩 벡터로 변환한다."""
    return embedder.embed_query(text)


def embed_texts(embedder: OpenAIEmbeddings, texts: list[str]) -> list[list[float]]:
    """여러 텍스트를 임베딩 벡터 리스트로 변환한다."""
    return embedder.embed_documents(texts)
