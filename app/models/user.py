import uuid
from sqlalchemy import Column, String, Boolean, SmallInteger, Double, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)       # null if Google OAuth only
    google_id = Column(String(255), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)
    phone_verified = Column(Boolean, default=False)

    name = Column(String(100), nullable=False)
    age = Column(SmallInteger, nullable=False)
    gender = Column(String(10), nullable=False)              # 'male' | 'female'
    bio = Column(Text, nullable=True)
    height = Column(SmallInteger, nullable=True)             # cm
    weight = Column(SmallInteger, nullable=True)             # kg

    lat = Column(Double, nullable=True)
    lng = Column(Double, nullable=True)

    is_premium = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    photos = relationship("Photo", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    daily_limits = relationship("DailyLimit", back_populates="user", cascade="all, delete-orphan")
    review_rewards = relationship("ReviewReward", back_populates="user", cascade="all, delete-orphan")
