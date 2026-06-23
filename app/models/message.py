# app/models/message.py
import uuid
from sqlalchemy import Column, Text, Boolean, DateTime, ForeignKey, func, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.core.encryption import encrypt_message, decrypt_message


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # match_id is nullable — messages can exist before a match (unmatched chat)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=True)
    
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Message content
    message_type = Column(String(20), default="text")  # 'text' | 'photo' | 'voice'
    _content = Column("content", Text, nullable=True)  # Stores encrypted content
    reply_to_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    
    # Media files
    media_url = Column(Text, nullable=True)
    media_duration = Column(Integer, nullable=True)  # for voice messages (seconds)
    media_size = Column(Integer, nullable=True)  # file size in bytes
    
    # Status tracking (Sent → Delivered → Read)
    is_sent = Column(Boolean, default=True)
    is_delivered = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    
    # Delete features
    is_deleted_for_sender = Column(Boolean, default=False)
    is_deleted_for_receiver = Column(Boolean, default=False)
    is_deleted_for_all = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Business Rule #4: unmatched chat — receiver must accept after 2 messages
    is_accepted = Column(Boolean, default=False)
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    match = relationship("Match", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
    reply_to = relationship("Message", remote_side=[id], foreign_keys=[reply_to_id])
    
    @property
    def content(self) -> str:
        """
        Decrypt content when accessed.
        """
        if not self._content or not self.match_id:
            return self._content
        
        try:
            # Decrypt using match_id
            return decrypt_message(self._content, str(self.match_id))
        except Exception as e:
            # If decryption fails, return encrypted content (for debugging)
            return self._content
    
    @content.setter
    def content(self, value: str):
        """
        Encrypt content before storing.
        """
        if value and self.match_id:
            try:
                # Encrypt using match_id
                self._content = encrypt_message(value, str(self.match_id))
            except Exception as e:
                # If encryption fails, store as-is (should not happen)
                self._content = value
        else:
            self._content = value
    
    def get_encrypted_content(self) -> str:
        """
        Get the raw encrypted content (for admin/debugging).
        """
        return self._content
    
    def get_decrypted_content_for_admin(self) -> str:
        """
        Decrypt content for admin review.
        """
        if not self._content or not self.match_id:
            return self._content
        return decrypt_message(self._content, str(self.match_id))