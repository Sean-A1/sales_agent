"""데이터 수집 — 리뷰 및 Q&A를 Qdrant에 upsert."""

from __future__ import annotations

import uuid

from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct

from src.rag.embeddings import embed_texts
from src.rag.qdrant_client import ensure_collection

COLLECTION_NAME = "product_reviews"


def ingest_reviews(
    client: QdrantClient,
    embedder: OpenAIEmbeddings,
    reviews: list[dict],
) -> int:
    """리뷰 텍스트를 임베딩 후 Qdrant에 upsert한다.

    Returns:
        upsert된 포인트 수.
    """
    if not reviews:
        return 0

    ensure_collection(client, COLLECTION_NAME)

    texts = [r["content"] for r in reviews]
    vectors = embed_texts(embedder, texts)

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload={
                "product_id": r["product_id"],
                "author": r.get("author", ""),
                "rating": r.get("rating", 0),
                "content": r["content"],
                "type": "review",
            },
        )
        for r, vec in zip(reviews, vectors)
    ]

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


def ingest_qna(
    client: QdrantClient,
    embedder: OpenAIEmbeddings,
    qna_list: list[dict],
) -> int:
    """Q&A 텍스트를 임베딩 후 Qdrant에 upsert한다.

    Returns:
        upsert된 포인트 수.
    """
    if not qna_list:
        return 0

    ensure_collection(client, COLLECTION_NAME)

    texts = [f"{q['question']} {q['answer']}" for q in qna_list]
    vectors = embed_texts(embedder, texts)

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload={
                "product_id": q["product_id"],
                "question": q["question"],
                "answer": q["answer"],
                "type": "qna",
            },
        )
        for q, vec in zip(qna_list, vectors)
    ]

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)
