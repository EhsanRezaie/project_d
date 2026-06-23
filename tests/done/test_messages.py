# tests/test_messages.py
import pytest
from httpx import AsyncClient
import base64
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import User

REGISTER_INIT_URL = "/api/v1/auth/register/init"
REGISTER_VERIFY_URL = "/api/v1/auth/register/verify"
REGISTER_COMPLETE_URL = "/api/v1/auth/register/complete"
SWIPE_URL = "/api/v1/swipes"
MESSAGES_URL = "/api/v1/messages"

VALID_EMAIL_MALE = "chat_male@example.com"
VALID_EMAIL_FEMALE = "chat_female@example.com"
VALID_PASSWORD = "strongpass123"
VALID_CODE = "123456"

COMPLETE_PROFILE_PAYLOAD_MALE = {
    "name": "Chat Male",
    "birth_date": "2000-01-01",
    "gender": "male",
    "lat": 35.6892,
    "lng": 51.3890,
    "sexual_orientation": "straight",
    "bio": "Test bio",
    "height": 180,
    "weight": 75,
}

COMPLETE_PROFILE_PAYLOAD_FEMALE = {
    "name": "Chat Female",
    "birth_date": "2000-01-01",
    "gender": "female",
    "lat": 35.6892,
    "lng": 51.3890,
    "sexual_orientation": "straight",
    "bio": "Test bio",
    "height": 165,
    "weight": 60,
}


async def register_user_full(
    client: AsyncClient,
    email: str,
    complete_payload: dict,
    mock_verification_code
) -> dict:
    """Complete full registration flow - returns user data with tokens."""
    # Step 1: Init
    res = await client.post(REGISTER_INIT_URL, json={"email": email})
    assert res.status_code == 200, res.text
    
    # Step 2: Store verification code
    await mock_verification_code(email, VALID_CODE)
    
    # Step 3: Verify
    res = await client.post(REGISTER_VERIFY_URL, json={
        "email": email,
        "code": VALID_CODE,
        "password": VALID_PASSWORD,
    })
    assert res.status_code == 200, res.text
    data = res.json()
    
    # Step 4: Complete profile
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    res = await client.post(
        REGISTER_COMPLETE_URL,
        json=complete_payload,
        headers=headers,
    )
    assert res.status_code == 200, res.text
    
    return res.json()


async def register_and_get_headers(
    client: AsyncClient,
    email: str,
    complete_payload: dict,
    mock_verification_code
) -> tuple[dict, str]:
    """Register a user and return headers with user_id."""
    result = await register_user_full(client, email, complete_payload, mock_verification_code)
    headers = {"Authorization": f"Bearer {result['access_token']}"}
    user_id = result["user"]["id"]
    return headers, user_id


def create_test_image() -> bytes:
    """Create a valid minimal JPEG image for testing."""
    import base64
    # This is a valid 1x1 JPEG
    return base64.b64decode(
        b"/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQ"
        b"EBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEB"
        b"AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QA"
        b"HwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIh"
        b"MUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVW"
        b"V1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXG"
        b"x8jJytLT1NXW19jZ2uLj5OXm5+jp6vLz9PX29/j5+v/EAB8BAAMBAQEBAQEBAQEAAAAAAAABAgMEBQYH"
        b"CAkKC//EALURAAIBAgQEAwQHBQQEAAECdwABAgMRBAUhMQYSQVEHYXETIjKBCBRCkaGxwQkjM1LwFWJy"
        b"0QoWJDThJfEXGBkaJicoKSo1Njc4OTpDREVGR0hJSlNUVVZXWFlaY2RlZmdoaWpzdHV2d3h5eoKDhIWG"
        b"h4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uLj5OXm5+jp6vLz"
        b"9PX29/j5+v/aAAwDAQACEQMRAD8A/wB4/wD/2Q=="
    )


def create_test_audio() -> bytes:
    """Create a minimal valid MP3 file for testing."""
    return base64.b64decode(
        b"SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAA"
        b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAASW5mbwAAAA8AAABIAAAADAAAVFRSU0UAAAAP"
        b"AAAAQVVESU8gQ09ERVgAAABMYXZmNTguNzYuMTAwAAAAAAAAAAAAAAD/"
    )


class TestMessages:
    """Test basic message functionality."""
    
    async def test_send_text_message_in_matched_chat(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should send text message in matched chat."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()
        
        # Create match
        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)
        match_res = await client.post(SWIPE_URL, json={"user_id": male_id, "direction": "like"}, headers=female_headers)
        match_id = match_res.json()["match_id"]

        # Send message
        res = await client.post(
            f"{MESSAGES_URL}/{match_id}/text",
            json={"content": "Hello!"},
            headers=male_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["id"] is not None
        assert data["chat_accepted"] == True

    async def test_get_chat_history(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should get chat history."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()

        # Create match and send message
        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)
        match_res = await client.post(SWIPE_URL, json={"user_id": male_id, "direction": "like"}, headers=female_headers)
        match_id = match_res.json()["match_id"]

        await client.post(f"{MESSAGES_URL}/{match_id}/text", json={"content": "Hello"}, headers=male_headers)

        # Get history
        res = await client.get(f"{MESSAGES_URL}/{match_id}", headers=male_headers)
        assert res.status_code == 200
        data = res.json()
        assert "messages" in data
        assert "total" in data

    async def test_unmatched_chat_limit(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should enforce 2 message limit in unmatched chat."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()

        # Like but no match yet
        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)

        # Send first message (should work)
        res1 = await client.post(
            f"{MESSAGES_URL}/{female_id}/text",
            json={"content": "First message"},
            headers=male_headers,
        )
        assert res1.status_code == 200

        # Send second message (should work)
        res2 = await client.post(
            f"{MESSAGES_URL}/{female_id}/text",
            json={"content": "Second message"},
            headers=male_headers,
        )
        assert res2.status_code == 200

        # Send third message (should fail)
        res3 = await client.post(
            f"{MESSAGES_URL}/{female_id}/text",
            json={"content": "Third message"},
            headers=male_headers,
        )
        assert res3.status_code == 403
        assert "must accept" in res3.json()["detail"]

    async def test_accept_chat(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should accept unmatched chat."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()

        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)

        # Send two messages (male to female)
        await client.post(f"{MESSAGES_URL}/{female_id}/text", json={"content": "Hi"}, headers=male_headers)
        await client.post(f"{MESSAGES_URL}/{female_id}/text", json={"content": "How are you?"}, headers=male_headers)

        # Accept chat - female accepts the chat from male
        res = await client.post(f"{MESSAGES_URL}/{male_id}/accept", headers=female_headers)
        assert res.status_code == 200
        assert res.json()["is_accepted"] == True

        # Now third message should work (male to female)
        res2 = await client.post(
            f"{MESSAGES_URL}/{female_id}/text",
            json={"content": "Third message after accept"},
            headers=male_headers,
        )
        assert res2.status_code == 200

    async def test_delete_message_for_me(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should delete message for me."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()

        # Create match
        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)
        match_res = await client.post(SWIPE_URL, json={"user_id": male_id, "direction": "like"}, headers=female_headers)
        match_id = match_res.json()["match_id"]

        # Send message
        msg_res = await client.post(
            f"{MESSAGES_URL}/{match_id}/text",
            json={"content": "Delete me"},
            headers=male_headers,
        )
        msg_id = msg_res.json()["id"]

        # Delete for me
        res = await client.delete(f"{MESSAGES_URL}/{msg_id}?delete_for=me", headers=male_headers)
        assert res.status_code == 200

    async def test_mark_messages_as_read(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should mark messages as read."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()

        # Create match and send message
        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)
        match_res = await client.post(SWIPE_URL, json={"user_id": male_id, "direction": "like"}, headers=female_headers)
        match_id = match_res.json()["match_id"]

        msg_res = await client.post(
            f"{MESSAGES_URL}/{match_id}/text",
            json={"content": "Read me"},
            headers=male_headers,
        )
        msg_id = msg_res.json()["id"]

        # Mark as read
        res = await client.post(
            f"{MESSAGES_URL}/read",
            json={"message_ids": [msg_id]},
            headers=female_headers,
        )
        assert res.status_code == 200

        # Check status
        status_res = await client.get(f"{MESSAGES_URL}/{msg_id}/status", headers=male_headers)
        assert status_res.status_code == 200
        assert status_res.json()["is_read"] == True


class TestPhotoMessages:
    """Test photo message functionality."""
    
    async def test_send_photo_in_matched_chat(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should send photo message in matched chat."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()

        # Create match
        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)
        match_res = await client.post(SWIPE_URL, json={"user_id": male_id, "direction": "like"}, headers=female_headers)
        match_id = match_res.json()["match_id"]

        # Send photo
        files = {"file": ("test.jpg", create_test_image(), "image/jpeg")}
        data = {"caption": "Check out this photo!"}
        
        res = await client.post(
            f"{MESSAGES_URL}/{match_id}/photo",
            files=files,
            data=data,
            headers=male_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["id"] is not None
        assert data["chat_accepted"] == True

    async def test_send_photo_in_unmatched_chat_fails(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should not allow photo in unmatched chat without acceptance."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()

        # Like but no match
        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)

        # Send photo without chat acceptance
        files = {"file": ("test.jpg", create_test_image(), "image/jpeg")}
        data = {"caption": "Photo without acceptance"}
        
        res = await client.post(
            f"{MESSAGES_URL}/{female_id}/photo",
            files=files,
            data=data,
            headers=male_headers,
        )
        assert res.status_code == 403
        assert "Photos can only be sent in accepted chats" in res.json()["detail"]

    async def test_send_photo_in_accepted_unmatched_chat(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should send photo in accepted unmatched chat."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()

        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)

        # Send two text messages
        await client.post(f"{MESSAGES_URL}/{female_id}/text", json={"content": "Hi"}, headers=male_headers)
        await client.post(f"{MESSAGES_URL}/{female_id}/text", json={"content": "How are you?"}, headers=male_headers)

        # Accept chat
        await client.post(f"{MESSAGES_URL}/{male_id}/accept", headers=female_headers)

        # Now send photo
        files = {"file": ("test.jpg", create_test_image(), "image/jpeg")}
        data = {"caption": "Photo after acceptance"}
        
        res = await client.post(
            f"{MESSAGES_URL}/{female_id}/photo",
            files=files,
            data=data,
            headers=male_headers,
        )
        assert res.status_code == 200
        assert res.json()["id"] is not None

    async def test_send_photo_without_caption(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should send photo without caption."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()

        # Create match
        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)
        match_res = await client.post(SWIPE_URL, json={"user_id": male_id, "direction": "like"}, headers=female_headers)
        match_id = match_res.json()["match_id"]

        # Send photo without caption
        files = {"file": ("test.jpg", create_test_image(), "image/jpeg")}
        
        res = await client.post(
            f"{MESSAGES_URL}/{match_id}/photo",
            files=files,
            headers=male_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["id"] is not None

    async def test_send_photo_too_large(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should reject photo larger than limit."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()

        # Create match
        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)
        match_res = await client.post(SWIPE_URL, json={"user_id": male_id, "direction": "like"}, headers=female_headers)
        match_id = match_res.json()["match_id"]

        # Create large image (6MB)
        large_image = b"0" * (6 * 1024 * 1024)  # 6MB
        files = {"file": ("test.jpg", large_image, "image/jpeg")}
        
        res = await client.post(
            f"{MESSAGES_URL}/{match_id}/photo",
            files=files,
            headers=male_headers,
        )
        assert res.status_code == 400
        assert "too large" in res.json()["detail"].lower()

    async def test_send_photo_invalid_format(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should reject invalid image format."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()

        # Create match
        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)
        match_res = await client.post(SWIPE_URL, json={"user_id": male_id, "direction": "like"}, headers=female_headers)
        match_id = match_res.json()["match_id"]

        # Send invalid format (GIF)
        invalid_image = b"GIF89a\x01\x00\x01\x00\x00\xff\x00\x00\x00\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01\x44\x00\x3b"
        files = {"file": ("test.gif", invalid_image, "image/gif")}
        
        res = await client.post(
            f"{MESSAGES_URL}/{match_id}/photo",
            files=files,
            headers=male_headers,
        )
        assert res.status_code == 400
        assert "invalid" in res.json()["detail"].lower()


class TestVoiceMessages:
    """Test voice message functionality."""
    
    async def test_send_voice_in_matched_chat(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should send voice message in matched chat."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()

        # Create match
        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)
        match_res = await client.post(SWIPE_URL, json={"user_id": male_id, "direction": "like"}, headers=female_headers)
        match_id = match_res.json()["match_id"]

        # Send voice
        files = {"file": ("test.mp3", create_test_audio(), "audio/mpeg")}
        data = {"duration": 15}
        
        res = await client.post(
            f"{MESSAGES_URL}/{match_id}/voice",
            files=files,
            data=data,
            headers=male_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["id"] is not None
        assert data["chat_accepted"] == True

    async def test_send_voice_in_unmatched_chat_fails(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should not allow voice in unmatched chat without acceptance."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()

        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)

        # Send voice without acceptance
        files = {"file": ("test.mp3", create_test_audio(), "audio/mpeg")}
        data = {"duration": 10}
        
        res = await client.post(
            f"{MESSAGES_URL}/{female_id}/voice",
            files=files,
            data=data,
            headers=male_headers,
        )
        assert res.status_code == 403
        assert "Voice messages can only be sent in accepted chats" in res.json()["detail"]

    async def test_send_voice_in_accepted_unmatched_chat(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should send voice in accepted unmatched chat."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()

        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)

        # Send two text messages and accept
        await client.post(f"{MESSAGES_URL}/{female_id}/text", json={"content": "Hi"}, headers=male_headers)
        await client.post(f"{MESSAGES_URL}/{female_id}/text", json={"content": "How are you?"}, headers=male_headers)
        await client.post(f"{MESSAGES_URL}/{male_id}/accept", headers=female_headers)

        # Send voice after acceptance
        files = {"file": ("test.mp3", create_test_audio(), "audio/mpeg")}
        data = {"duration": 10}
        
        res = await client.post(
            f"{MESSAGES_URL}/{female_id}/voice",
            files=files,
            data=data,
            headers=male_headers,
        )
        assert res.status_code == 200
        assert res.json()["id"] is not None

    async def test_send_voice_too_long(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should reject voice longer than limit."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()

        # Create match
        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)
        match_res = await client.post(SWIPE_URL, json={"user_id": male_id, "direction": "like"}, headers=female_headers)
        match_id = match_res.json()["match_id"]

        # Send voice with duration > 120 seconds
        files = {"file": ("test.mp3", create_test_audio(), "audio/mpeg")}
        data = {"duration": 150}
        
        res = await client.post(
            f"{MESSAGES_URL}/{match_id}/voice",
            files=files,
            data=data,
            headers=male_headers,
        )
        assert res.status_code == 400
        assert "too long" in res.json()["detail"].lower()

    async def test_send_voice_too_large(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should reject voice larger than limit."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()

        # Create match
        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)
        match_res = await client.post(SWIPE_URL, json={"user_id": male_id, "direction": "like"}, headers=female_headers)
        match_id = match_res.json()["match_id"]

        # Create large voice (3MB)
        large_voice = b"0" * (3 * 1024 * 1024)  # 3MB
        files = {"file": ("test.mp3", large_voice, "audio/mpeg")}
        data = {"duration": 10}
        
        res = await client.post(
            f"{MESSAGES_URL}/{match_id}/voice",
            files=files,
            data=data,
            headers=male_headers,
        )
        assert res.status_code == 400
        assert "too large" in res.json()["detail"].lower()


class TestMediaInChatHistory:
    """Test that media appears correctly in chat history."""
    
    async def test_chat_history_contains_photo(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should include photo URL in chat history."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()

        # Create match
        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)
        match_res = await client.post(SWIPE_URL, json={"user_id": male_id, "direction": "like"}, headers=female_headers)
        match_id = match_res.json()["match_id"]

        # Send photo
        files = {"file": ("test.jpg", create_test_image(), "image/jpeg")}
        data = {"caption": "Test photo"}
        
        await client.post(
            f"{MESSAGES_URL}/{match_id}/photo",
            files=files,
            data=data,
            headers=male_headers,
        )

        # Get history
        res = await client.get(f"{MESSAGES_URL}/{match_id}", headers=male_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data["messages"]) >= 1
        
        # Check photo message fields
        photo_msg = next((m for m in data["messages"] if m["message_type"] == "photo"), None)
        assert photo_msg is not None
        assert photo_msg["media_url"] is not None
        assert photo_msg["content"] == "Test photo"

    async def test_chat_history_contains_voice(
        self, 
        client: AsyncClient, 
        mock_verification_code,
        db_session
    ):
        """Should include voice URL and duration in chat history."""
        male_headers, male_id = await register_and_get_headers(
            client, VALID_EMAIL_MALE, COMPLETE_PROFILE_PAYLOAD_MALE, mock_verification_code
        )
        female_headers, female_id = await register_and_get_headers(
            client, VALID_EMAIL_FEMALE, COMPLETE_PROFILE_PAYLOAD_FEMALE, mock_verification_code
        )

        # ✅ Ensure profiles are loaded
        result = await db_session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_([male_id, female_id]))
        )
        users = result.scalars().all()

        # Create match
        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)
        match_res = await client.post(SWIPE_URL, json={"user_id": male_id, "direction": "like"}, headers=female_headers)
        match_id = match_res.json()["match_id"]

        # Send voice
        files = {"file": ("test.mp3", create_test_audio(), "audio/mpeg")}
        data = {"duration": 15}
        
        await client.post(
            f"{MESSAGES_URL}/{match_id}/voice",
            files=files,
            data=data,
            headers=male_headers,
        )

        # Get history
        res = await client.get(f"{MESSAGES_URL}/{match_id}", headers=male_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data["messages"]) >= 1
        
        # Check voice message fields
        voice_msg = next((m for m in data["messages"] if m["message_type"] == "voice"), None)
        assert voice_msg is not None
        assert voice_msg["media_url"] is not None
        assert voice_msg["media_duration"] == 15