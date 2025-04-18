import logging
import sys
from pathlib import Path
from types import FrameType
from typing import cast

from loguru import logger


class InterceptHandler(logging.Handler):
    """
    Обработчик для перехвата стандартных логов Python
    и перенаправления их в loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = cast(FrameType, frame.f_back)
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging(log_level: str = "INFO") -> None:
    """
    Настраивает логирование для приложения.
    
    Args:
        log_level: Уровень логирования
    """
    logger.remove()

    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level=log_level,
        colorize=True,
    )

    logs_path = Path("logs")
    logs_path.mkdir(exist_ok=True)
    logger.add(
        logs_path / "delivery_service.log",
        rotation="10 MB",  # Ротация по размеру
        retention="7 days",  # Хранение логов - неделя
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    for logger_name in ("uvicorn", "uvicorn.error", "fastapi"):
        logging.getLogger(logger_name).handlers = [InterceptHandler()]


app_logger = logger
