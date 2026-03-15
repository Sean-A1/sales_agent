"""RAG layer unit tests — Qdrant·OpenAI 연결 없이 Mock 기반 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_qdrant():
    """Mock QdrantClient."""
    client = MagicMock()
    # get_collections returns empty by default
    collections_resp = MagicMock()
    collections_resp.collections = []
    client.get_collections.return_value = collections_resp
    return client


@pytest.fixture
def mock_embedder():
    """Mock OpenAIEmbeddings."""
    embedder = MagicMock()
    embedder.embed_query.return_value = [0.1] * 1536
    embedder.embed_documents.return_value = [[0.1] * 1536, [0.2] * 1536]
    return embedder


# ---------------------------------------------------------------------------
# qdrant_client tests
# ---------------------------------------------------------------------------

class TestQdrantClient:

    @patch("src.rag.qdrant_client.get_settings")
    @patch("src.rag.qdrant_client.QdrantClient")
    def test_get_qdrant_client(self, mock_cls, mock_settings):
        from src.rag.qdrant_client import get_qdrant_client

        mock_settings.return_value = MagicMock(
            QDRANT_URL="http://localhost:6333",
            QDRANT_API_KEY="test-key",
        )

        client = get_qdrant_client()

        mock_cls.assert_called_once_with(
            url="http://localhost:6333",
            api_key="test-key",
        )
        assert client is not None

    @patch("src.rag.qdrant_client.get_settings")
    @patch("src.rag.qdrant_client.QdrantClient")
    def test_get_qdrant_client_no_api_key(self, mock_cls, mock_settings):
        from src.rag.qdrant_client import get_qdrant_client

        mock_settings.return_value = MagicMock(
            QDRANT_URL="http://localhost:6333",
            QDRANT_API_KEY="",
        )

        get_qdrant_client()

        mock_cls.assert_called_once_with(
            url="http://localhost:6333",
            api_key=None,
        )

    def test_ensure_collection_creates(self, mock_qdrant):
        from src.rag.qdrant_client import ensure_collection

        ensure_collection(mock_qdrant, "test_collection", vector_size=1536)

        mock_qdrant.create_collection.assert_called_once()
        call_kwargs = mock_qdrant.create_collection.call_args[1]
        assert call_kwargs["collection_name"] == "test_collection"

    def test_ensure_collection_exists(self, mock_qdrant):
        from src.rag.qdrant_client import ensure_collection

        existing = MagicMock()
        existing.name = "test_collection"
        mock_qdrant.get_collections.return_value.collections = [existing]

        ensure_collection(mock_qdrant, "test_collection")

        mock_qdrant.create_collection.assert_not_called()


# ---------------------------------------------------------------------------
# embeddings tests
# ---------------------------------------------------------------------------

class TestEmbeddings:

    @patch("src.rag.embeddings.OpenAIEmbeddings")
    def test_get_embedder(self, mock_cls):
        from src.core import get_settings
        from src.rag.embeddings import get_embedder

        get_embedder()

        mock_cls.assert_called_once_with(
            model="text-embedding-3-small",
            api_key=get_settings().OPENAI_API_KEY,
        )

    def test_embed_text(self, mock_embedder):
        from src.rag.embeddings import embed_text

        result = embed_text(mock_embedder, "좋은 상품입니다")

        mock_embedder.embed_query.assert_called_once_with("좋은 상품입니다")
        assert len(result) == 1536

    def test_embed_texts(self, mock_embedder):
        from src.rag.embeddings import embed_texts

        result = embed_texts(mock_embedder, ["텍스트1", "텍스트2"])

        mock_embedder.embed_documents.assert_called_once_with(["텍스트1", "텍스트2"])
        assert len(result) == 2


# ---------------------------------------------------------------------------
# ingest tests
# ---------------------------------------------------------------------------

class TestIngest:

    def test_ingest_reviews(self, mock_qdrant, mock_embedder):
        from src.rag.ingest import ingest_reviews

        reviews = [
            {"product_id": 1, "author": "홍길동", "rating": 5, "content": "최고의 상품"},
            {"product_id": 1, "author": "김철수", "rating": 4, "content": "괜찮습니다"},
        ]

        count = ingest_reviews(mock_qdrant, mock_embedder, reviews)

        assert count == 2
        mock_embedder.embed_documents.assert_called_once()
        mock_qdrant.upsert.assert_called_once()
        points = mock_qdrant.upsert.call_args[1]["points"]
        assert len(points) == 2
        assert points[0].payload["type"] == "review"
        assert points[0].payload["product_id"] == 1

    def test_ingest_reviews_empty(self, mock_qdrant, mock_embedder):
        from src.rag.ingest import ingest_reviews

        count = ingest_reviews(mock_qdrant, mock_embedder, [])

        assert count == 0
        mock_qdrant.upsert.assert_not_called()

    def test_ingest_qna(self, mock_qdrant, mock_embedder):
        from src.rag.ingest import ingest_qna

        qna_list = [
            {"product_id": 1, "question": "배터리 수명?", "answer": "약 10시간"},
            {"product_id": 1, "question": "색상 옵션?", "answer": "블랙, 화이트"},
        ]

        count = ingest_qna(mock_qdrant, mock_embedder, qna_list)

        assert count == 2
        mock_qdrant.upsert.assert_called_once()
        points = mock_qdrant.upsert.call_args[1]["points"]
        assert points[0].payload["type"] == "qna"
        assert points[0].payload["question"] == "배터리 수명?"

    def test_ingest_qna_empty(self, mock_qdrant, mock_embedder):
        from src.rag.ingest import ingest_qna

        count = ingest_qna(mock_qdrant, mock_embedder, [])

        assert count == 0
        mock_qdrant.upsert.assert_not_called()


# ---------------------------------------------------------------------------
# search tests
# ---------------------------------------------------------------------------

class TestSearch:

    def _make_hit(self, payload: dict, score: float) -> MagicMock:
        hit = MagicMock()
        hit.payload = payload
        hit.score = score
        return hit

    def test_search_reviews(self, mock_qdrant, mock_embedder):
        from src.rag.search import search_reviews

        qp_result = MagicMock()
        qp_result.points = [
            self._make_hit({"content": "좋아요", "type": "review"}, 0.95),
            self._make_hit({"content": "괜찮아요", "type": "review"}, 0.85),
        ]
        mock_qdrant.query_points.return_value = qp_result

        results = search_reviews(mock_qdrant, mock_embedder, "이 상품 어때요?")

        assert len(results) == 2
        assert results[0]["score"] == 0.95
        assert results[0]["payload"]["content"] == "좋아요"
        mock_qdrant.query_points.assert_called_once()

    def test_search_reviews_with_product_id(self, mock_qdrant, mock_embedder):
        from src.rag.search import search_reviews

        qp_result = MagicMock()
        qp_result.points = []
        mock_qdrant.query_points.return_value = qp_result

        search_reviews(mock_qdrant, mock_embedder, "배터리", product_id=1, limit=3)

        call_kwargs = mock_qdrant.query_points.call_args[1]
        assert call_kwargs["limit"] == 3
        filter_obj = call_kwargs["query_filter"]
        assert len(filter_obj.must) == 2  # type + product_id

    def test_search_reviews_no_product_id(self, mock_qdrant, mock_embedder):
        from src.rag.search import search_reviews

        qp_result = MagicMock()
        qp_result.points = []
        mock_qdrant.query_points.return_value = qp_result

        search_reviews(mock_qdrant, mock_embedder, "배터리")

        call_kwargs = mock_qdrant.query_points.call_args[1]
        filter_obj = call_kwargs["query_filter"]
        assert len(filter_obj.must) == 1  # type only

    def test_search_qna(self, mock_qdrant, mock_embedder):
        from src.rag.search import search_qna

        qp_result = MagicMock()
        qp_result.points = [
            self._make_hit(
                {"question": "무게?", "answer": "200g", "type": "qna"}, 0.9,
            ),
        ]
        mock_qdrant.query_points.return_value = qp_result

        results = search_qna(mock_qdrant, mock_embedder, "무게가 얼마나 되나요?")

        assert len(results) == 1
        assert results[0]["payload"]["answer"] == "200g"

    def test_search_qna_with_product_id(self, mock_qdrant, mock_embedder):
        from src.rag.search import search_qna

        qp_result = MagicMock()
        qp_result.points = []
        mock_qdrant.query_points.return_value = qp_result

        search_qna(mock_qdrant, mock_embedder, "색상?", product_id=2)

        call_kwargs = mock_qdrant.query_points.call_args[1]
        filter_obj = call_kwargs["query_filter"]
        assert len(filter_obj.must) == 2


# ---------------------------------------------------------------------------
# __init__ re-export tests
# ---------------------------------------------------------------------------

class TestInit:

    def test_all_exports(self):
        import src.rag as rag

        expected = [
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
        for name in expected:
            assert hasattr(rag, name), f"{name} not exported from src.rag"
