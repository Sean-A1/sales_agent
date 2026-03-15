"""src.core 레이어 테스트."""

import os

from src.core.config import Settings, get_settings
from src.core.logging import get_logger


# ── config ────────────────────────────────────────────


class TestSettings:
    def test_default_values(self):
        """기본값이 올바르게 설정되는지 확인."""
        settings = Settings(
            _env_file=None,  # .env 무시, 순수 기본값 테스트
        )
        assert settings.QDRANT_URL == "http://localhost:6333"
        assert settings.POSTGRES_USER == "sales_agent"
        assert settings.POSTGRES_DB == "sales_agent"

    def test_env_override(self, monkeypatch):
        """환경변수가 기본값을 덮어쓰는지 확인."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        monkeypatch.setenv("NEO4J_URI", "bolt://localhost:7687")

        settings = Settings(_env_file=None)
        assert settings.OPENAI_API_KEY == "test-key-123"
        assert settings.NEO4J_URI == "bolt://localhost:7687"

    def test_get_settings_singleton(self):
        """get_settings()가 동일 인스턴스를 반환하는지 확인."""
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
        get_settings.cache_clear()


# ── logging ───────────────────────────────────────────


class TestLogger:
    def test_get_logger_returns_logger(self):
        """get_logger()가 loguru 로거를 반환하는지 확인."""
        log = get_logger("test_module")
        assert callable(log.info)
        assert callable(log.debug)

    def test_logger_writes(self):
        """로거가 메시지를 출력하는지 확인."""
        messages: list[str] = []
        from loguru import logger

        sink_id = logger.add(lambda m: messages.append(m), level="INFO")
        try:
            log = get_logger("test_write")
            log.info("hello core")
            assert any("hello core" in m for m in messages)
        finally:
            logger.remove(sink_id)
