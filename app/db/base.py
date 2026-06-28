from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime, func
import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.core.logging import get_logger

logger = get_logger("db.base")


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
