"""Conversation context management via Neo4j session graph."""

from __future__ import annotations

from neo4j import AsyncDriver

from src.graph.neo4j_client import execute_query


async def create_session_context(
    driver: AsyncDriver,
    session_id: str,
) -> dict:
    """Create a conversation session node."""
    query = """
    MERGE (s:Session {session_id: $session_id})
    RETURN s {.*} AS session
    """
    records = await execute_query(driver, query, {"session_id": session_id})
    return records[0]["session"] if records else {}


async def add_context_condition(
    driver: AsyncDriver,
    session_id: str,
    key: str,
    value: str,
) -> None:
    """Add (Session)-[:HAS_CONDITION]->(Condition) edge.

    Example: key="budget", value="300000"
    """
    query = """
    MERGE (s:Session {session_id: $session_id})
    MERGE (cond:Condition {key: $key, session_id: $session_id})
    SET cond.value = $value
    MERGE (s)-[:HAS_CONDITION]->(cond)
    """
    await execute_query(
        driver, query, {"session_id": session_id, "key": key, "value": value},
    )


async def get_session_context(
    driver: AsyncDriver,
    session_id: str,
) -> dict:
    """Return all conditions for a session as {key: value} dict."""
    query = """
    MATCH (s:Session {session_id: $session_id})-[:HAS_CONDITION]->(cond:Condition)
    RETURN cond.key AS key, cond.value AS value
    """
    records = await execute_query(driver, query, {"session_id": session_id})
    return {r["key"]: r["value"] for r in records}


async def clear_session_context(
    driver: AsyncDriver,
    session_id: str,
) -> None:
    """Delete session node and all connected conditions."""
    query = """
    MATCH (s:Session {session_id: $session_id})
    OPTIONAL MATCH (s)-[:HAS_CONDITION]->(cond:Condition)
    DETACH DELETE s, cond
    """
    await execute_query(driver, query, {"session_id": session_id})
