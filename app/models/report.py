import uuid
from sqlalchemy import Column, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reported_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
