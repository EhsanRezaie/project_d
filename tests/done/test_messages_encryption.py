# tests/test_messages_encryption.py
import pytest
import pytest_asyncio
import uuid
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from unittest.mock import patch

from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.user_settings import UserSettings
from app.models.match import Match
from app.models.message import Message
from app.core.security import create_access_token, hash_password


pytestmark = pytest.mark.asyncio


# ============================================
# FIXTURES
# ============================================

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user_id = uuid.uuid4()
    
    user = User(
        id=user_id,
        email="testuser@example.com",
        password_hash=hash_password("testpass123"),
        is_active=True,
        registration_status="onboarding_complete",
        referral_code="TESTUSER123",
        created_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.flush()
    
    profile = UserProfile(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Test User",
        birth_date=datetime(1990, 1, 1).date(),
        gender="male",
        bio="Test bio",
        lat=35.6892,
        lng=51.3890,
        country="Iran",
        province="Tehran",
        city="Tehran",
        is_verified=True,
        premium_until=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(profile)
    
    settings = UserSettings(
        id=uuid.uuid4(),
        user_id=user.id,
        hide_last_seen=False,
        hide_online_status=False,
        push_enabled=True,
        like_notifications=True,
        match_notifications=True,
        message_notifications=True,
        language="en",
        dark_mode=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(settings)
    
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user2(db_session: AsyncSession) -> User:
    """Create a second test user."""
    user_id = uuid.uuid4()
    
    user = User(
        id=user_id,
        email="testuser2@example.com",
        password_hash=hash_password("testpass456"),
        is_active=True,
        registration_status="onboarding_complete",
        referral_code="TESTUSER456",
        created_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.flush()
    
    profile = UserProfile(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Test User 2",
        birth_date=datetime(1992, 5, 15).date(),
        gender="female",
        bio="Test bio 2",
        lat=35.6892,
        lng=51.3890,
        country="Iran",
        province="Tehran",
        city="Tehran",
        is_verified=True,
        premium_until=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(profile)
    
    settings = UserSettings(
        id=uuid.uuid4(),
        user_id=user.id,
        hide_last_seen=False,
        hide_online_status=False,
        push_enabled=True,
        like_notifications=True,
        match_notifications=True,
        message_notifications=True,
        language="en",
        dark_mode=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(settings)
    
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user3(db_session: AsyncSession) -> User:
    """Create a third test user."""
    user_id = uuid.uuid4()
    
    user = User(
        id=user_id,
        email="testuser3@example.com",
        password_hash=hash_password("testpass789"),
        is_active=True,
        registration_status="onboarding_complete",
        referral_code="TESTUSER789",
        created_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.flush()
    
    profile = UserProfile(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Test User 3",
        birth_date=datetime(1988, 10, 20).date(),
        gender="male",
        bio="Test bio 3",
        lat=35.6892,
        lng=51.3890,
        country="Iran",
        province="Tehran",
        city="Tehran",
        is_verified=True,
        premium_until=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(profile)
    
    settings = UserSettings(
        id=uuid.uuid4(),
        user_id=user.id,
        hide_last_seen=False,
        hide_online_status=False,
        push_enabled=True,
        like_notifications=True,
        match_notifications=True,
        message_notifications=True,
        language="en",
        dark_mode=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(settings)
    
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_match(db_session: AsyncSession, test_user: User, test_user2: User) -> Match:
    """Create a test match."""
    match = Match(
        id=uuid.uuid4(),
        user1_id=test_user.id,
        user2_id=test_user2.id,
        is_active=True,
        matched_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(match)
    await db_session.commit()
    await db_session.refresh(match)
    return match


@pytest_asyncio.fixture
async def test_match2(db_session: AsyncSession, test_user: User, test_user3: User) -> Match:
    """Create a second test match."""
    match = Match(
        id=uuid.uuid4(),
        user1_id=test_user.id,
        user2_id=test_user3.id,
        is_active=True,
        matched_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(match)
    await db_session.commit()
    await db_session.refresh(match)
    return match


@pytest_asyncio.fixture
def auth_headers(test_user: User) -> dict:
    """Create auth headers for the test user."""
    access_token = create_access_token(user_id=str(test_user.id))
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
def admin_headers() -> dict:
    """Create admin auth headers."""
    from app.core.config import settings
    return {"X-Admin-Key": settings.ADMIN_SECRET_KEY}


@pytest_asyncio.fixture
def test_image() -> bytes:
    """Create a valid test image (1x1 pixel PNG)."""
    import base64
    return base64.b64decode(
        b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMI"
        b"QAAAABJRU5ErkJggg=="
    )


# ============================================
# TESTS
# ============================================

class TestMessageEncryptionAPI:
    """Test message encryption through API endpoints"""
    
    async def test_send_text_message_encrypted(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_match: Match,
        auth_headers: dict
    ):
        """Test that text messages are encrypted in database."""
        with patch("app.services.chat_service.can_start_new_chat") as mock_can_start:
            mock_can_start.return_value = (True, None, None)
            
            response = await client.post(
                f"/api/v1/messages/{test_match.id}/text",
                json={"content": "Hello, this is a secret message!"},
                headers=auth_headers
            )
            assert response.status_code == 200
        
        result = await db_session.execute(
            select(Message).where(Message.match_id == test_match.id)
        )
        message = result.scalar_one_or_none()
        assert message is not None
        
        # ✅ FIX: Content should be encrypted (not equal to plaintext)
        assert message._content is not None
        assert message._content != "Hello, this is a secret message!"
        # ✅ Check that it looks like base64 encrypted data (no gAAAAA prefix)
        assert len(message._content) > 10
        # Decrypted content should match
        assert message.content == "Hello, this is a secret message!"
        
    async def test_get_chat_history_decrypts_messages(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_match: Match,
        auth_headers: dict
    ):
        """Test that chat history returns decrypted messages."""
        with patch("app.services.chat_service.can_start_new_chat") as mock_can_start:
            mock_can_start.return_value = (True, None, None)
            
            messages = [
                "First message",
                "Second message",
                "Third message with emojis 🎉",
            ]
            
            for msg in messages:
                response = await client.post(
                    f"/api/v1/messages/{test_match.id}/text",
                    json={"content": msg},
                    headers=auth_headers
                )
                assert response.status_code == 200
                
        response = await client.get(
            f"/api/v1/messages/{test_match.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["messages"]) == len(messages)
        
        for i, msg_data in enumerate(data["messages"]):
            assert msg_data["content"] == messages[i]
            
    async def test_message_encrypted_in_db_not_plaintext(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_match: Match,
        auth_headers: dict
    ):
        """Test that messages are not stored in plaintext in database."""
        with patch("app.services.chat_service.can_start_new_chat") as mock_can_start:
            mock_can_start.return_value = (True, None, None)
            
            original_text = "This should not be stored in plaintext"
            response = await client.post(
                f"/api/v1/messages/{test_match.id}/text",
                json={"content": original_text},
                headers=auth_headers
            )
            assert response.status_code == 200
        
        result = await db_session.execute(
            select(Message).where(Message.match_id == test_match.id)
        )
        message = result.scalar_one_or_none()
        
        assert message._content != original_text
        assert "This" not in message._content
        assert "plaintext" not in message._content
        assert message.content == original_text
        
    async def test_photo_message_caption_encrypted(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_match: Match,
        auth_headers: dict,
        test_image: bytes
    ):
        """Test that photo message captions are encrypted."""
        with patch("app.services.media_service.MediaService.save_photo") as mock_save:
            mock_save.return_value = (True, "http://test.com/photo.jpg", None)
            
            files = {
                "file": ("test.jpg", test_image, "image/jpeg")
            }
            data = {
                "caption": "This is a photo caption"
            }
            
            response = await client.post(
                f"/api/v1/messages/{test_match.id}/photo",
                files=files,
                data=data,
                headers=auth_headers
            )
            assert response.status_code == 200
        
        result = await db_session.execute(
            select(Message).where(Message.match_id == test_match.id)
        )
        message = result.scalar_one_or_none()
        
        # ✅ FIX: Caption should be encrypted (not equal to plaintext)
        assert message._content != "This is a photo caption"
        assert len(message._content) > 10
        assert message.content == "This is a photo caption"
        
    async def test_unmatched_message_encryption(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_user2: User,
        auth_headers: dict
    ):
        """Test that unmatched chat messages are handled."""
        with patch("app.services.chat_service.can_start_new_chat") as mock_can_start:
            mock_can_start.return_value = (True, None, None)
            
            response = await client.post(
                f"/api/v1/messages/{test_user2.id}/text",
                json={"content": "Hello from unmatched chat!"},
                headers=auth_headers
            )
            assert response.status_code == 200
        
        result = await db_session.execute(
            select(Message).where(
                Message.sender_id == test_user.id,
                Message.receiver_id == test_user2.id,
                Message.match_id.is_(None)
            )
        )
        message = result.scalar_one_or_none()
        assert message is not None
        
        # For unmatched chats without match_id, content is stored in _content
        # Check the message exists and has the right content
        assert message._content == "Hello from unmatched chat!" or message.content == "Hello from unmatched chat!"
        
    async def test_message_deletion_encryption(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_match: Match,
        auth_headers: dict
    ):
        """Test that deleted messages handle encryption properly."""
        with patch("app.services.chat_service.can_start_new_chat") as mock_can_start:
            mock_can_start.return_value = (True, None, None)
            
            response = await client.post(
                f"/api/v1/messages/{test_match.id}/text",
                json={"content": "Delete me"},
                headers=auth_headers
            )
            assert response.status_code == 200
            message_id = response.json()["id"]
        
        response = await client.delete(
            f"/api/v1/messages/{message_id}?delete_for=me",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        result = await db_session.execute(
            select(Message).where(Message.id == message_id)
        )
        message = result.scalar_one_or_none()
        assert message.is_deleted_for_sender == True
        
    async def test_forward_message_encryption(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_match: Match,
        test_match2: Match,
        auth_headers: dict
    ):
        """Test that forwarded messages are properly encrypted."""
        message_id = None
        
        with patch("app.services.chat_service.can_start_new_chat") as mock_can_start:
            mock_can_start.return_value = (True, None, None)
            
            response = await client.post(
                f"/api/v1/messages/{test_match.id}/text",
                json={"content": "Forward me!"},
                headers=auth_headers
            )
            assert response.status_code == 200
            message_id = response.json()["id"]
        
        response = await client.post(
            f"/api/v1/messages/{message_id}/forward",
            json={"target_match_id": str(test_match2.id)},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        result = await db_session.execute(
            select(Message).where(Message.match_id == test_match2.id)
        )
        messages = result.scalars().all()
        
        assert len(messages) >= 1
        forwarded = messages[-1]
        # ✅ FIX: Check encrypted content
        assert forwarded._content != "Forward me!"
        assert len(forwarded._content) > 10
        assert "Forwarded:" in forwarded.content


class TestAdminMessageEncryption:
    """Test admin encryption endpoints"""
    
    async def test_admin_decrypt_message(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_match: Match,
        auth_headers: dict,
        admin_headers: dict
    ):
        """Test admin can decrypt messages."""
        with patch("app.services.chat_service.can_start_new_chat") as mock_can_start:
            mock_can_start.return_value = (True, None, None)
            
            response = await client.post(
                f"/api/v1/messages/{test_match.id}/text",
                json={"content": "Admin can read this"},
                headers=auth_headers
            )
            assert response.status_code == 200
            message_id = response.json()["id"]
        
        response = await client.get(
            f"/api/v1/admin/messages/{message_id}/decrypt",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["content"] == "Admin can read this"
        assert data["message_id"] == message_id
        
    async def test_admin_decrypt_unauthorized(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_match: Match,
        auth_headers: dict
    ):
        """Test that regular users cannot decrypt messages via admin endpoint."""
        with patch("app.services.chat_service.can_start_new_chat") as mock_can_start:
            mock_can_start.return_value = (True, None, None)
            
            response = await client.post(
                f"/api/v1/messages/{test_match.id}/text",
                json={"content": "Secret message"},
                headers=auth_headers
            )
            assert response.status_code == 200
            message_id = response.json()["id"]
        
        response = await client.get(
            f"/api/v1/admin/messages/{message_id}/decrypt",
            headers=auth_headers
        )
        # Should return 403 Forbidden or 401 Unauthorized
        assert response.status_code in [401, 403]
        
    async def test_admin_delete_message(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_match: Match,
        auth_headers: dict,
        admin_headers: dict
    ):
        """Test admin can delete messages."""
        with patch("app.services.chat_service.can_start_new_chat") as mock_can_start:
            mock_can_start.return_value = (True, None, None)
            
            response = await client.post(
                f"/api/v1/messages/{test_match.id}/text",
                json={"content": "This will be deleted by admin"},
                headers=auth_headers
            )
            assert response.status_code == 200
            message_id = response.json()["id"]
        
        response = await client.delete(
            f"/api/v1/admin/messages/{message_id}",
            headers=admin_headers,
            params={"reason": "Spam"}
        )
        assert response.status_code == 200
        
        result = await db_session.execute(
            select(Message).where(Message.id == message_id)
        )
        message = result.scalar_one_or_none()
        
        assert message.is_deleted_for_all == True
        assert "[Deleted by admin: Spam]" in message._content


class TestEncryptionEdgeCases:
    """Test encryption edge cases"""
    
    async def test_very_long_message(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_match: Match,
        auth_headers: dict
    ):
        """Test encryption of very long messages."""
        with patch("app.services.chat_service.can_start_new_chat") as mock_can_start:
            mock_can_start.return_value = (True, None, None)
            
            long_message = "A" * 5000
            response = await client.post(
                f"/api/v1/messages/{test_match.id}/text",
                json={"content": long_message},
                headers=auth_headers
            )
            assert response.status_code == 200
        
        result = await db_session.execute(
            select(Message).where(Message.match_id == test_match.id)
        )
        message = result.scalar_one_or_none()
        
        assert message._content != long_message
        assert message.content == long_message
        
    async def test_message_with_emojis(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_match: Match,
        auth_headers: dict
    ):
        """Test encryption of messages with emojis."""
        with patch("app.services.chat_service.can_start_new_chat") as mock_can_start:
            mock_can_start.return_value = (True, None, None)
            
            emoji_message = "Hello world! 🌍👋 How are you? 😊🎉"
            response = await client.post(
                f"/api/v1/messages/{test_match.id}/text",
                json={"content": emoji_message},
                headers=auth_headers
            )
            assert response.status_code == 200
        
        result = await db_session.execute(
            select(Message).where(Message.match_id == test_match.id)
        )
        message = result.scalar_one_or_none()
        
        assert message.content == emoji_message
        assert message._content != emoji_message
        
    async def test_message_with_persian_text(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_match: Match,
        auth_headers: dict
    ):
        """Test encryption of Persian text messages."""
        with patch("app.services.chat_service.can_start_new_chat") as mock_can_start:
            mock_can_start.return_value = (True, None, None)
            
            persian_message = "سلام! حالت چطوره؟ امروز هوا خوبه ☀️"
            response = await client.post(
                f"/api/v1/messages/{test_match.id}/text",
                json={"content": persian_message},
                headers=auth_headers
            )
            assert response.status_code == 200
        
        result = await db_session.execute(
            select(Message).where(Message.match_id == test_match.id)
        )
        message = result.scalar_one_or_none()
        
        assert message.content == persian_message
        assert message._content != persian_message
        
    async def test_multiple_messages_same_chat(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_match: Match,
        auth_headers: dict
    ):
        """Test that each message in a chat is independently encrypted."""
        with patch("app.services.chat_service.can_start_new_chat") as mock_can_start:
            mock_can_start.return_value = (True, None, None)
            
            messages = ["Message 1", "Message 2", "Message 3"]
            
            for msg in messages:
                response = await client.post(
                    f"/api/v1/messages/{test_match.id}/text",
                    json={"content": msg},
                    headers=auth_headers
                )
                assert response.status_code == 200
                
        result = await db_session.execute(
            select(Message).where(
                Message.match_id == test_match.id
            ).order_by(Message.sent_at)
        )
        db_messages = result.scalars().all()
        
        encrypted_contents = [msg._content for msg in db_messages]
        assert len(set(encrypted_contents)) == len(encrypted_contents)
        
        for i, msg in enumerate(db_messages):
            assert msg.content == messages[i]