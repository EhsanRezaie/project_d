import logging
import sys
from typing import Optional

from app.core.config import settings

# Logging configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log levels
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def setup_logging(level: Optional[str] = None) -> None:
    """Configure logging for the entire application."""
    log_level = level or ("DEBUG" if settings.DEBUG else "INFO")
    log_level_num = LOG_LEVELS.get(log_level.lower(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level_num)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler (for development)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level_num)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    root_logger.addHandler(console_handler)
    
    # File handler (for production)
    if not settings.DEBUG:
        file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
        file_handler.setLevel(log_level_num)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        root_logger.addHandler(file_handler)
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    # Custom loggers
    logging.getLogger("app.core.redis").setLevel(log_level_num)
    logging.getLogger("app.api.auth").setLevel(log_level_num)
    
    # Suppress noisy libraries
    logging.getLogger("passlib").setLevel(logging.WARNING)
    logging.getLogger("jose").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module."""
    return logging.getLogger(f"app.{name}")


# Create logs directory if it doesn't exist
import os
if not os.path.exists("logs"):
    os.makedirs("logs", exist_ok=True)