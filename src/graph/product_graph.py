"""Product knowledge graph — nodes, relationships, and traversal queries."""

from __future__ import annotations

from neo4j import AsyncDriver

from src.graph.neo4j_client import execute_query


async def create_product_node(
    driver: AsyncDriver,
    product_id: int,
    name: str,
    category: str,
    brand: str,
    price: int,
    specs: dict | None = None,
) -> dict:
    """Create or update a Product node (MERGE on product_id)."""
    query = """
    MERGE (p:Product {product_id: $product_id})
    SET p.name = $name,
        p.category = $category,
        p.brand = $brand,
        p.price = $price,
        p.specs = $specs
    RETURN p {.*} AS product
    """
    params = {
        "product_id": product_id,
        "name": name,
        "category": category,
        "brand": brand,
        "price": price,
        "specs": str(specs) if specs else None,
    }
    records = await execute_query(driver, query, params)
    return records[0]["product"] if records else {}


async def create_category_relationship(
    driver: AsyncDriver,
    product_id: int,
    category: str,
) -> None:
    """Create (Product)-[:BELONGS_TO]->(Category) relationship."""
    query = """
    MERGE (p:Product {product_id: $product_id})
    MERGE (c:Category {name: $category})
    MERGE (p)-[:BELONGS_TO]->(c)
    """
    await execute_query(driver, query, {"product_id": product_id, "category": category})


async def get_related_products(
    driver: AsyncDriver,
    product_id: int,
    limit: int = 5,
) -> list[dict]:
    """Get related products in the same category (excluding self)."""
    query = """
    MATCH (p:Product {product_id: $product_id})-[:BELONGS_TO]->(c:Category)
          <-[:BELONGS_TO]-(related:Product)
    WHERE related.product_id <> $product_id
    RETURN related {.*} AS product
    LIMIT $limit
    """
    return await execute_query(
        driver, query, {"product_id": product_id, "limit": limit},
    )


async def get_products_by_category(
    driver: AsyncDriver,
    category: str,
    limit: int = 10,
) -> list[dict]:
    """Get products belonging to a category."""
    query = """
    MATCH (p:Product)-[:BELONGS_TO]->(c:Category {name: $category})
    RETURN p {.*} AS product
    LIMIT $limit
    """
    return await execute_query(
        driver, query, {"category": category, "limit": limit},
    )
