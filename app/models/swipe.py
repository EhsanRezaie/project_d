import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class Swipe(Base):
    __tablename__ = "swipes"
    __table_args__ = (UniqueConstraint("from_user", "to_user"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_user = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    to_user = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    direction = Column(String(10), nullable=False)           # 'like' | 'pass'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
