import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, String, Boolean, SmallInteger, Double, DateTime, Text, func, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    google_id = Column(String(255), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)
    phone_verified = Column(Boolean, default=False)

    name = Column(String(100), nullable=False)
    age = Column(SmallInteger, nullable=False)
    gender = Column(String(10), nullable=False)
    bio = Column(Text, nullable=True)
    height = Column(SmallInteger, nullable=True)
    weight = Column(SmallInteger, nullable=True)

    lat = Column(Double, nullable=True)
    lng = Column(Double, nullable=True)

    premium_until = Column(DateTime(timezone=True), nullable=True)
    
    is_active = Column(Boolean, default=True)
    token_version = Column(Integer, default=1, nullable=False)
    is_profile_complete = Column(Boolean, default=True)

    referral_code = Column(String(20), unique=True, nullable=True)
    referred_by = Column(UUID(as_uuid=True), nullable=True)

    hide_last_seen = Column(Boolean, default=False)
    hide_online_status = Column(Boolean, default=False)

    country = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    location_manual = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    photos = relationship("Photo", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    daily_limits = relationship("DailyLimit", back_populates="user", cascade="all, delete-orphan")
    review_rewards = relationship("ReviewReward", back_populates="user", cascade="all, delete-orphan")
    sent_swipes = relationship("Swipe", foreign_keys="Swipe.from_user", back_populates="from_user_rel", cascade="all, delete-orphan")
    received_swipes = relationship("Swipe", foreign_keys="Swipe.to_user", back_populates="to_user_rel", cascade="all, delete-orphan")
    matches_as_user1 = relationship("Match", foreign_keys="Match.user1_id", back_populates="user1")
    matches_as_user2 = relationship("Match", foreign_keys="Match.user2_id", back_populates="user2")
    
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="user", cascade="all, delete-orphan")
    sent_reports = relationship("Report", foreign_keys="Report.reporter_id", back_populates="reporter", cascade="all, delete-orphan")
    received_reports = relationship("Report", foreign_keys="Report.reported_id", back_populates="reported", cascade="all, delete-orphan")
    
    referral_rewards_given = relationship("ReferralReward", foreign_keys="ReferralReward.inviter_id", back_populates="inviter")
    referral_rewards_received = relationship("ReferralReward", foreign_keys="ReferralReward.invited_id", back_populates="invited")

    @property
    def is_premium(self) -> bool:
        """Check if user has active premium subscription."""
        if self.premium_until is None:
            return False
        now = datetime.now(timezone.utc)
        return self.premium_until > now
    
    def add_premium_days(self, days: int):
        """Add premium days to existing premium or set new expiry."""
        now = datetime.now(timezone.utc)
        if self.premium_until is None or self.premium_until < now:
            self.premium_until = now + timedelta(days=days)
        else:
            self.premium_until = self.premium_until + timedelta(days=days)