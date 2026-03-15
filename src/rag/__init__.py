"""RAG 파이프라인 — Qdrant 기반 리뷰 & Q&A 임베딩 검색."""

from src.rag.embeddings import embed_text, embed_texts, get_embedder
from src.rag.ingest import COLLECTION_NAME, ingest_qna, ingest_reviews
from src.rag.qdrant_client import ensure_collection, get_qdrant_client
from src.rag.search import search_qna, search_reviews

__all__ = [
    "get_qdrant_client",
    "ensure_collection",
    "get_embedder",
    "embed_text",
    "embed_texts",
    "ingest_reviews",
    "ingest_qna",
    "COLLECTION_NAME",
    "search_reviews",
    "search_qna",
]
