import uuid
from sqlalchemy import Column, String, Boolean, SmallInteger, Text, ForeignKey
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

    # Moderation fields (Business Rule #5)
    status = Column(String(20), default="pending")          # 'pending' | 'approved' | 'rejected'
    reject_reason = Column(Text, nullable=True)             # populated if status = 'rejected'

    # Face verification (Business Rule #6)
    face_verified = Column(Boolean, default=False)

    user = relationship("User", back_populates="photos")
