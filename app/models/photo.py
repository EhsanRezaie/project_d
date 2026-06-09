import uuid
from sqlalchemy import Column, String, Boolean, SmallInteger, ForeignKey
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

    user = relationship("User", back_populates="photos")
