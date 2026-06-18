import uuid
from sqlalchemy import Column, String, Text , Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    category = Column(String(30), nullable=True)  # about_me, lifestyle, etc.
    is_active = Column(Boolean, default=True)

    # Relationships
    user_prompts = relationship("UserPrompt", back_populates="prompt", cascade="all, delete-orphan")