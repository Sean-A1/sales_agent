"""앱 설정 — pydantic BaseSettings 기반 .env 로드."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    OPENAI_API_KEY: str = ""

    # Neo4j
    NEO4J_URI: str = ""
    NEO4J_USERNAME: str = ""
    NEO4J_PASSWORD: str = ""

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""

    # PostgreSQL
    POSTGRES_USER: str = "sales_agent"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "sales_agent"
    DATABASE_URL: str = "postgresql://sales_agent:@localhost:5432/sales_agent"


@lru_cache
def get_settings() -> Settings:
    """싱글톤 Settings 인스턴스를 반환한다."""
    return Settings()
