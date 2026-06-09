from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime, func
import uuid
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
