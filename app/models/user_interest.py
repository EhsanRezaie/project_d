import uuid
from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class UserInterest(Base):
    __tablename__ = "user_interests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    interest_id = Column(UUID(as_uuid=True), ForeignKey("interests.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "interest_id", name="uq_user_interests_user_interest"),
    )

    # Relationships
    user = relationship("User", back_populates="user_interests")
    interest = relationship("Interest", back_populates="user_interests")