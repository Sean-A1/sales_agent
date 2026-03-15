"""Graph layer unit tests — Neo4j 연결 없이 Mock 기반 테스트."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_driver():
    """Mock AsyncDriver with session context manager."""
    driver = MagicMock()
    mock_session = AsyncMock()
    ctx = AsyncMock()
    ctx.__aenter__.return_value = mock_session
    ctx.__aexit__.return_value = False
    driver.session.return_value = ctx
    return driver


def _setup_query_result(mock_driver, records: list[dict]):
    """Configure mock driver to return given records from a query."""
    mock_session = AsyncMock()
    mock_result = AsyncMock()

    # Make result async-iterable over record objects
    mock_records = []
    for rec in records:
        mock_record = MagicMock()
        mock_record.data.return_value = rec
        mock_records.append(mock_record)

    # Build a proper async iterator
    async def _aiter():
        for r in mock_records:
            yield r

    mock_result.__aiter__ = lambda self: _aiter()
    mock_session.run = AsyncMock(return_value=mock_result)

    ctx = AsyncMock()
    ctx.__aenter__.return_value = mock_session
    ctx.__aexit__.return_value = False
    mock_driver.session.return_value = ctx

    return mock_session


# ---------------------------------------------------------------------------
# neo4j_client tests
# ---------------------------------------------------------------------------

class TestNeo4jClient:

    @patch("src.graph.neo4j_client.get_settings")
    @patch("src.graph.neo4j_client.AsyncGraphDatabase")
    def test_get_driver(self, mock_gdb, mock_settings):
        from src.graph.neo4j_client import get_driver

        mock_settings.return_value = MagicMock(
            NEO4J_URI="bolt://localhost:7687",
            NEO4J_USERNAME="neo4j",
            NEO4J_PASSWORD="test",
        )
        mock_gdb.driver.return_value = MagicMock()

        driver = get_driver()

        mock_gdb.driver.assert_called_once_with(
            "bolt://localhost:7687",
            auth=("neo4j", "test"),
        )
        assert driver is not None

    @pytest.mark.asyncio
    async def test_close_driver(self):
        from src.graph.neo4j_client import close_driver

        driver = AsyncMock()
        await close_driver(driver)
        driver.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_query(self, mock_driver):
        from src.graph.neo4j_client import execute_query

        expected = [{"name": "테스트 상품"}]
        _setup_query_result(mock_driver, expected)

        results = await execute_query(mock_driver, "MATCH (n) RETURN n", {"id": 1})

        assert results == expected

    @pytest.mark.asyncio
    async def test_execute_query_empty(self, mock_driver):
        from src.graph.neo4j_client import execute_query

        _setup_query_result(mock_driver, [])

        results = await execute_query(mock_driver, "MATCH (n) RETURN n")

        assert results == []


# ---------------------------------------------------------------------------
# product_graph tests
# ---------------------------------------------------------------------------

class TestProductGraph:

    @pytest.mark.asyncio
    @patch("src.graph.product_graph.execute_query")
    async def test_create_product_node(self, mock_eq):
        from src.graph.product_graph import create_product_node

        mock_eq.return_value = [{"product": {
            "product_id": 1,
            "name": "삼성 갤럭시 S25",
            "category": "스마트폰",
            "brand": "삼성",
            "price": 1200000,
        }}]

        result = await create_product_node(
            driver=AsyncMock(),
            product_id=1,
            name="삼성 갤럭시 S25",
            category="스마트폰",
            brand="삼성",
            price=1200000,
            specs={"ram": "12GB"},
        )

        assert result["product_id"] == 1
        assert result["name"] == "삼성 갤럭시 S25"
        mock_eq.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.graph.product_graph.execute_query")
    async def test_create_product_node_empty(self, mock_eq):
        from src.graph.product_graph import create_product_node

        mock_eq.return_value = []

        result = await create_product_node(
            driver=AsyncMock(),
            product_id=99,
            name="없는 상품",
            category="기타",
            brand="기타",
            price=0,
        )

        assert result == {}

    @pytest.mark.asyncio
    @patch("src.graph.product_graph.execute_query")
    async def test_create_category_relationship(self, mock_eq):
        from src.graph.product_graph import create_category_relationship

        mock_eq.return_value = []

        await create_category_relationship(
            driver=AsyncMock(),
            product_id=1,
            category="스마트폰",
        )

        mock_eq.assert_awaited_once()
        call_args = mock_eq.call_args
        assert "BELONGS_TO" in call_args[0][1]

    @pytest.mark.asyncio
    @patch("src.graph.product_graph.execute_query")
    async def test_get_related_products(self, mock_eq):
        from src.graph.product_graph import get_related_products

        mock_eq.return_value = [
            {"product": {"product_id": 2, "name": "아이폰 16"}},
            {"product": {"product_id": 3, "name": "갤럭시 Z 플립"}},
        ]

        results = await get_related_products(driver=AsyncMock(), product_id=1, limit=5)

        assert len(results) == 2
        assert results[0]["product"]["name"] == "아이폰 16"

    @pytest.mark.asyncio
    @patch("src.graph.product_graph.execute_query")
    async def test_get_products_by_category(self, mock_eq):
        from src.graph.product_graph import get_products_by_category

        mock_eq.return_value = [
            {"product": {"product_id": 1, "name": "삼성 갤럭시 S25"}},
        ]

        results = await get_products_by_category(
            driver=AsyncMock(), category="스마트폰", limit=10,
        )

        assert len(results) == 1
        call_args = mock_eq.call_args
        assert call_args[0][2]["category"] == "스마트폰"


# ---------------------------------------------------------------------------
# context_graph tests
# ---------------------------------------------------------------------------

class TestContextGraph:

    @pytest.mark.asyncio
    @patch("src.graph.context_graph.execute_query")
    async def test_create_session_context(self, mock_eq):
        from src.graph.context_graph import create_session_context

        mock_eq.return_value = [{"session": {"session_id": "sess-001"}}]

        result = await create_session_context(driver=AsyncMock(), session_id="sess-001")

        assert result["session_id"] == "sess-001"
        mock_eq.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.graph.context_graph.execute_query")
    async def test_create_session_context_empty(self, mock_eq):
        from src.graph.context_graph import create_session_context

        mock_eq.return_value = []

        result = await create_session_context(driver=AsyncMock(), session_id="sess-999")

        assert result == {}

    @pytest.mark.asyncio
    @patch("src.graph.context_graph.execute_query")
    async def test_add_context_condition(self, mock_eq):
        from src.graph.context_graph import add_context_condition

        mock_eq.return_value = []

        await add_context_condition(
            driver=AsyncMock(),
            session_id="sess-001",
            key="budget",
            value="300000",
        )

        mock_eq.assert_awaited_once()
        call_args = mock_eq.call_args
        assert call_args[0][2]["key"] == "budget"
        assert call_args[0][2]["value"] == "300000"

    @pytest.mark.asyncio
    @patch("src.graph.context_graph.execute_query")
    async def test_get_session_context(self, mock_eq):
        from src.graph.context_graph import get_session_context

        mock_eq.return_value = [
            {"key": "budget", "value": "300000"},
            {"key": "category", "value": "스마트폰"},
        ]

        result = await get_session_context(driver=AsyncMock(), session_id="sess-001")

        assert result == {"budget": "300000", "category": "스마트폰"}

    @pytest.mark.asyncio
    @patch("src.graph.context_graph.execute_query")
    async def test_get_session_context_empty(self, mock_eq):
        from src.graph.context_graph import get_session_context

        mock_eq.return_value = []

        result = await get_session_context(driver=AsyncMock(), session_id="sess-999")

        assert result == {}

    @pytest.mark.asyncio
    @patch("src.graph.context_graph.execute_query")
    async def test_clear_session_context(self, mock_eq):
        from src.graph.context_graph import clear_session_context

        mock_eq.return_value = []

        await clear_session_context(driver=AsyncMock(), session_id="sess-001")

        mock_eq.assert_awaited_once()
        call_args = mock_eq.call_args
        assert "DETACH DELETE" in call_args[0][1]
