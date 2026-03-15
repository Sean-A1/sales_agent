"""시맨틱 검색 — 리뷰 및 Q&A 쿼리."""

from __future__ import annotations

from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import FieldCondition, Filter, MatchValue

from src.rag.embeddings import embed_text
from src.rag.ingest import COLLECTION_NAME


def _build_filter(product_id: int | None, doc_type: str) -> Filter:
    """product_id 및 type 필터를 구성한다."""
    conditions = [FieldCondition(key="type", match=MatchValue(value=doc_type))]
    if product_id is not None:
        conditions.append(
            FieldCondition(key="product_id", match=MatchValue(value=product_id))
        )
    return Filter(must=conditions)


def search_reviews(
    client: QdrantClient,
    embedder: OpenAIEmbeddings,
    query: str,
    product_id: int | None = None,
    limit: int = 5,
) -> list[dict]:
    """리뷰 시맨틱 검색. payload + score 반환."""
    vector = embed_text(embedder, query)
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        query_filter=_build_filter(product_id, "review"),
        limit=limit,
    )
    return [{"payload": hit.payload, "score": hit.score} for hit in results]


def search_qna(
    client: QdrantClient,
    embedder: OpenAIEmbeddings,
    query: str,
    product_id: int | None = None,
    limit: int = 3,
) -> list[dict]:
    """Q&A 시맨틱 검색. payload + score 반환."""
    vector = embed_text(embedder, query)
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        query_filter=_build_filter(product_id, "qna"),
        limit=limit,
    )
    return [{"payload": hit.payload, "score": hit.score} for hit in results]
