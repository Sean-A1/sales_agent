"""loguru 기반 로거 설정."""

import sys

from loguru import logger

# 기본 핸들러(stderr) 제거 후 재설정
logger.remove()

# 콘솔: INFO 이상
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
)

# 파일: DEBUG 이상, 10 MB rotation
logger.add(
    "logs/app.log",
    level="DEBUG",
    rotation="10 MB",
    retention="7 days",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function} - {message}",
)


def get_logger(name: str = __name__) -> logger.__class__:
    """모듈별 바인딩 로거를 반환한다."""
    return logger.bind(name=name)
