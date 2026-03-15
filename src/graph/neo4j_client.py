"""Neo4j async driver connection and query execution."""

from __future__ import annotations

from neo4j import AsyncGraphDatabase, AsyncDriver

from src.core import get_settings, get_logger

logger = get_logger(__name__)


def get_driver() -> AsyncDriver:
    """Create and return an async Neo4j driver."""
    settings = get_settings()
    driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
    )
    logger.info("Neo4j driver created for {}", settings.NEO4J_URI)
    return driver


async def close_driver(driver: AsyncDriver) -> None:
    """Close the Neo4j driver."""
    await driver.close()
    logger.info("Neo4j driver closed")


async def execute_query(
    driver: AsyncDriver,
    query: str,
    params: dict | None = None,
) -> list[dict]:
    """Execute a Cypher query and return results as list of dicts."""
    async with driver.session() as session:
        result = await session.run(query, parameters=params or {})
        records = [record.data() async for record in result]
        return records
