import uuid
from sqlalchemy import Column, String, Boolean, SmallInteger, Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class Photo(Base):
    __tablename__ = "photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    order = Column(SmallInteger, default=0)
    is_main = Column(Boolean, default=False)

    # Moderation fields
    status = Column(String(20), default="pending")
    reject_reason = Column(Text, nullable=True)

    # Face verification
    face_verified = Column(Boolean, default=False)
    
    # Add created_at if missing
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="photos")