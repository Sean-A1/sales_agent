"""Tests for agent layer — intent, nodes, graph."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent.state import AgentState
from src.agent.intent import classify_intent, INTENTS, SYSTEM_PROMPT, _CONTEXT_KEYS
from src.agent.nodes import (
    search_node,
    recommend_node,
    detail_node,
    stock_node,
    review_node,
    cart_node,
    order_track_node,
    unknown_node,
    _last_user_message,
)
from src.agent.graph import build_graph, _route_by_intent, INTENT_TO_NODE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(**overrides) -> AgentState:
    defaults: AgentState = {
        "session_id": "test-session",
        "messages": [{"role": "user", "content": "노트북 검색해줘"}],
        "intent": "",
        "context": {},
        "result": {},
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class TestAgentState:
    def test_state_fields(self):
        state = _make_state()
        assert state["session_id"] == "test-session"
        assert state["messages"][0]["role"] == "user"
        assert state["intent"] == ""
        assert state["context"] == {}
        assert state["result"] == {}


# ---------------------------------------------------------------------------
# Intent Classification
# ---------------------------------------------------------------------------

class TestClassifyIntent:
    @pytest.mark.asyncio
    @patch("src.agent.intent.AsyncOpenAI")
    async def test_classify_search(self, mock_openai_cls):
        mock_client = AsyncMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"intent": "search", "query": "노트북"}'
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        state = _make_state(messages=[{"role": "user", "content": "노트북 찾아줘"}])
        result = await classify_intent(state)

        assert result["intent"] == "search"
        assert result["context"]["query"] == "노트북"
        mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.agent.intent.AsyncOpenAI")
    async def test_classify_recommend_with_category(self, mock_openai_cls):
        mock_client = AsyncMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = (
            '{"intent": "recommend", "category": "가전/디지털", "query": "청소기"}'
        )
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        state = _make_state(messages=[{"role": "user", "content": "청소기 추천해줘"}])
        result = await classify_intent(state)

        assert result["intent"] == "recommend"
        assert result["context"]["category"] == "가전/디지털"
        assert result["context"]["query"] == "청소기"

    @pytest.mark.asyncio
    @patch("src.agent.intent.AsyncOpenAI")
    async def test_classify_unknown_fallback(self, mock_openai_cls):
        mock_client = AsyncMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"intent": "invalid_intent"}'
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        state = _make_state()
        result = await classify_intent(state)

        assert result["intent"] == "unknown"
        assert result["context"] == {}

    @pytest.mark.asyncio
    @patch("src.agent.intent.AsyncOpenAI")
    async def test_classify_json_parse_error(self, mock_openai_cls):
        mock_client = AsyncMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "not json"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        state = _make_state()
        result = await classify_intent(state)

        assert result["intent"] == "unknown"
        assert result["context"] == {}

    @pytest.mark.asyncio
    @patch("src.agent.intent.AsyncOpenAI")
    async def test_context_only_includes_known_keys(self, mock_openai_cls):
        mock_client = AsyncMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = (
            '{"intent": "detail", "product_id": 42, "extra_field": "ignored"}'
        )
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        state = _make_state(messages=[{"role": "user", "content": "상품 42번 상세 보여줘"}])
        result = await classify_intent(state)

        assert result["intent"] == "detail"
        assert result["context"] == {"product_id": 42}
        assert "extra_field" not in result["context"]

    @pytest.mark.asyncio
    async def test_classify_no_user_message(self):
        state = _make_state(messages=[{"role": "assistant", "content": "안녕하세요"}])
        result = await classify_intent(state)

        assert result["intent"] == "unknown"
        assert result["context"] == {}

    def test_intents_list(self):
        assert "search" in INTENTS
        assert "recommend" in INTENTS
        assert "unknown" in INTENTS
        assert len(INTENTS) == 8

    def test_system_prompt_contains_intents(self):
        for intent in INTENTS:
            assert intent in SYSTEM_PROMPT

    def test_context_keys_defined(self):
        assert "category" in _CONTEXT_KEYS
        assert "query" in _CONTEXT_KEYS
        assert "product_id" in _CONTEXT_KEYS
        assert "order_id" in _CONTEXT_KEYS


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

class TestSearchNode:
    @pytest.mark.asyncio
    @patch("src.agent.nodes.get_session")
    @patch("src.agent.nodes.get_engine")
    async def test_search_returns_products(self, mock_engine, mock_get_session):
        mock_product = MagicMock()
        mock_product.id = 1
        mock_product.name = "맥북 프로"
        mock_product.category = "노트북"
        mock_product.price = 2_000_000
        mock_product.stock = 10

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_product]
        mock_session.exec = AsyncMock(return_value=mock_result)

        async def fake_get_session(engine):
            yield mock_session

        mock_get_session.side_effect = fake_get_session

        state = _make_state(
            messages=[{"role": "user", "content": "노트북 검색해줘"}],
            context={"query": "노트북"},
        )
        result = await search_node(state)

        assert result["result"]["type"] == "search"
        assert len(result["result"]["products"]) == 1
        assert result["result"]["products"][0]["name"] == "맥북 프로"


class TestRecommendNode:
    @pytest.mark.asyncio
    @patch("src.agent.nodes.get_driver")
    @patch("src.agent.nodes.execute_query")
    async def test_recommend_with_category(self, mock_exec, mock_driver):
        driver = AsyncMock()
        mock_driver.return_value = driver
        mock_exec.return_value = [
            {"product": {"product_id": 1, "name": "노트북A", "category": "노트북",
                         "brand": "삼성", "price": 1_500_000}}
        ]

        state = _make_state(context={"category": "노트북"})
        result = await recommend_node(state)

        assert result["result"]["type"] == "recommend"
        assert len(result["result"]["products"]) == 1

    @pytest.mark.asyncio
    @patch("src.agent.nodes.get_driver")
    @patch("src.agent.nodes.execute_query")
    async def test_recommend_no_category(self, mock_exec, mock_driver):
        driver = AsyncMock()
        mock_driver.return_value = driver
        mock_exec.return_value = []

        state = _make_state()
        result = await recommend_node(state)

        assert result["result"]["type"] == "recommend"
        assert result["result"]["products"] == []


class TestDetailNode:
    @pytest.mark.asyncio
    @patch("src.agent.nodes.get_session")
    @patch("src.agent.nodes.get_engine")
    async def test_detail_found(self, mock_engine, mock_get_session):
        mock_product = MagicMock()
        mock_product.id = 1
        mock_product.name = "맥북 프로"
        mock_product.description = "애플 노트북"
        mock_product.category = "노트북"
        mock_product.brand = "애플"
        mock_product.price = 2_000_000
        mock_product.stock = 5
        mock_product.specs = {"cpu": "M3"}

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_product)

        async def fake_get_session(engine):
            yield mock_session

        mock_get_session.side_effect = fake_get_session

        state = _make_state(context={"product_id": 1})
        result = await detail_node(state)

        assert result["result"]["type"] == "detail"
        assert result["result"]["product"]["name"] == "맥북 프로"

    @pytest.mark.asyncio
    async def test_detail_no_product_id(self):
        state = _make_state()
        result = await detail_node(state)

        assert result["result"]["type"] == "detail"
        assert "error" in result["result"]


class TestStockNode:
    @pytest.mark.asyncio
    @patch("src.agent.nodes.get_session")
    @patch("src.agent.nodes.get_engine")
    async def test_stock_in_stock(self, mock_engine, mock_get_session):
        mock_product = MagicMock()
        mock_product.id = 1
        mock_product.name = "마우스"
        mock_product.price = 50_000
        mock_product.stock = 20

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_product)

        async def fake_get_session(engine):
            yield mock_session

        mock_get_session.side_effect = fake_get_session

        state = _make_state(context={"product_id": 1})
        result = await stock_node(state)

        assert result["result"]["type"] == "stock"
        assert result["result"]["in_stock"] is True
        assert result["result"]["stock"] == 20

    @pytest.mark.asyncio
    async def test_stock_no_product_id(self):
        state = _make_state()
        result = await stock_node(state)

        assert "error" in result["result"]


class TestReviewNode:
    @pytest.mark.asyncio
    @patch("src.agent.nodes.search_qna")
    @patch("src.agent.nodes.search_reviews")
    @patch("src.agent.nodes.get_embedder")
    @patch("src.agent.nodes.get_qdrant_client")
    async def test_review_search(self, mock_qdrant, mock_embedder,
                                  mock_search_reviews, mock_search_qna):
        mock_search_reviews.return_value = [
            {"payload": {"content": "좋은 제품"}, "score": 0.9}
        ]
        mock_search_qna.return_value = []

        state = _make_state(
            messages=[{"role": "user", "content": "리뷰 알려줘"}],
            context={"product_id": 1},
        )
        result = await review_node(state)

        assert result["result"]["type"] == "review"
        assert len(result["result"]["reviews"]) == 1


class TestCartNode:
    @pytest.mark.asyncio
    @patch("src.agent.nodes.get_session")
    @patch("src.agent.nodes.get_engine")
    async def test_cart_add(self, mock_engine, mock_get_session):
        mock_session = AsyncMock()

        async def fake_get_session(engine):
            yield mock_session

        mock_get_session.side_effect = fake_get_session

        state = _make_state(context={"product_id": 1, "quantity": 2})
        result = await cart_node(state)

        assert result["result"]["type"] == "cart"
        assert result["result"]["action"] == "added"
        assert result["result"]["quantity"] == 2

    @pytest.mark.asyncio
    @patch("src.agent.nodes.get_session")
    @patch("src.agent.nodes.get_engine")
    async def test_cart_list(self, mock_engine, mock_get_session):
        mock_item = MagicMock()
        mock_item.product_id = 1
        mock_item.quantity = 3

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_item]
        mock_session.exec = AsyncMock(return_value=mock_result)

        async def fake_get_session(engine):
            yield mock_session

        mock_get_session.side_effect = fake_get_session

        state = _make_state()
        result = await cart_node(state)

        assert result["result"]["type"] == "cart"
        assert result["result"]["action"] == "list"
        assert len(result["result"]["items"]) == 1


class TestOrderTrackNode:
    @pytest.mark.asyncio
    @patch("src.agent.nodes.get_session")
    @patch("src.agent.nodes.get_engine")
    async def test_order_found(self, mock_engine, mock_get_session):
        from datetime import datetime, UTC

        mock_order = MagicMock()
        mock_order.id = 100
        mock_order.status = "SHIPPING"
        mock_order.total_price = 500_000
        mock_order.created_at = datetime(2026, 1, 1, tzinfo=UTC)

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_order)

        async def fake_get_session(engine):
            yield mock_session

        mock_get_session.side_effect = fake_get_session

        state = _make_state(context={"order_id": 100})
        result = await order_track_node(state)

        assert result["result"]["type"] == "order_track"
        assert result["result"]["status"] == "SHIPPING"

    @pytest.mark.asyncio
    async def test_order_no_id(self):
        state = _make_state()
        result = await order_track_node(state)

        assert "error" in result["result"]


class TestUnknownNode:
    @pytest.mark.asyncio
    async def test_unknown_response(self):
        state = _make_state()
        result = await unknown_node(state)

        assert result["result"]["type"] == "unknown"
        assert "message" in result["result"]


class TestLastUserMessage:
    def test_extracts_last_user_msg(self):
        state = _make_state(messages=[
            {"role": "user", "content": "첫 번째"},
            {"role": "assistant", "content": "응답"},
            {"role": "user", "content": "두 번째"},
        ])
        assert _last_user_message(state) == "두 번째"

    def test_no_user_message(self):
        state = _make_state(messages=[{"role": "assistant", "content": "응답"}])
        assert _last_user_message(state) == ""


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

class TestRouteByIntent:
    def test_routes_all_intents(self):
        for intent in INTENTS:
            state = _make_state(intent=intent)
            node = _route_by_intent(state)
            assert node in INTENT_TO_NODE.values()

    def test_unknown_fallback(self):
        state = _make_state(intent="nonexistent")
        assert _route_by_intent(state) == "unknown"


class TestBuildGraph:
    def test_graph_compiles(self):
        graph = build_graph()
        assert graph is not None

    def test_graph_has_nodes(self):
        graph = build_graph()
        node_names = set(graph.get_graph().nodes.keys())
        expected = {
            "classify_intent", "search", "recommend", "detail",
            "stock", "review", "cart", "order_track", "unknown",
        }
        assert expected.issubset(node_names)

    def test_intent_to_node_mapping(self):
        assert len(INTENT_TO_NODE) == 8
        assert INTENT_TO_NODE["search"] == "search"
        assert INTENT_TO_NODE["unknown"] == "unknown"


# ---------------------------------------------------------------------------
# __init__ re-exports
# ---------------------------------------------------------------------------

class TestAgentInit:
    def test_exports(self):
        from src.agent import build_graph, AgentState
        assert callable(build_graph)
        assert AgentState is not None
