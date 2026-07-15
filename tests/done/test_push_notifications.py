# tests/test_push_notifications.py

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

REGISTER_INIT_URL = "/api/v1/auth/register/init"
REGISTER_VERIFY_URL = "/api/v1/auth/register/verify"
REGISTER_COMPLETE_URL = "/api/v1/auth/register/complete"
DEVICE_TOKEN_URL = "/api/v1/notifications/device-token"
SWIPE_URL = "/api/v1/swipes"
MESSAGES_URL = "/api/v1/messages"

VALID_EMAIL = "push_test@example.com"
VALID_EMAIL_2 = "push_test2@example.com"
VALID_PASSWORD = "strongpass123"
VALID_CODE = "123456"

COMPLETE_PROFILE_PAYLOAD = {
    "name": "Push Test User",
    "birth_date": "2000-01-01",
    "gender": "male",
    "lat": 35.6892,
    "lng": 51.3890,
    "sexual_orientation": "straight",
    "bio": "Test user",
    "height": 180,
    "weight": 75,
    "body_type": "athletic",
    "relationship_status": "single",
    "living_situation": "alone",
    "children_status": "dont_have",
    "smoking": "never",
    "drinking": "socially",
    "education": "bachelor",
    "workplace": "Tech",
    "religion": "islam",
    "ethnicity": "persian",
    "political_orientation": "moderate",
    "languages": ["persian", "english"],
    "country": "Iran",
    "province": "Tehran",
    "city": "Tehran",
}

COMPLETE_PROFILE_PAYLOAD_2 = {
    "name": "Push Test User 2",
    "birth_date": "1998-05-15",
    "gender": "female",
    "lat": 35.6892,
    "lng": 51.3890,
    "sexual_orientation": "straight",
    "bio": "Test user 2",
    "height": 165,
    "weight": 60,
    "body_type": "slim",
    "relationship_status": "single",
    "living_situation": "with_family",
    "children_status": "dont_have",
    "smoking": "never",
    "drinking": "never",
    "education": "master",
    "workplace": "Hospital",
    "religion": "islam",
    "ethnicity": "persian",
    "political_orientation": "moderate",
    "languages": ["persian", "english"],
    "country": "Iran",
    "province": "Tehran",
    "city": "Tehran",
}


async def register_user(client, email, payload, mock_verification_code):
    """Register a user and return tokens."""
    res = await client.post(REGISTER_INIT_URL, json={"email": email})
    assert res.status_code == 200, res.text

    await mock_verification_code(email, VALID_CODE)

    res = await client.post(REGISTER_VERIFY_URL, json={
        "email": email,
        "code": VALID_CODE,
        "password": VALID_PASSWORD,
    })
    assert res.status_code == 200, res.text
    data = res.json()

    headers = {"Authorization": f"Bearer {data['access_token']}"}
    res = await client.post(REGISTER_COMPLETE_URL, json=payload, headers=headers)
    assert res.status_code == 200, res.text

    return res.json()


class TestDeviceToken:

    async def test_register_device_token(self, client, mock_verification_code):
        """Should register a device token."""
        result = await register_user(client, VALID_EMAIL, COMPLETE_PROFILE_PAYLOAD, mock_verification_code)
        headers = {"Authorization": f"Bearer {result['access_token']}"}

        res = await client.post(
            DEVICE_TOKEN_URL,
            json={"token": "firebase-token-123", "platform": "android"},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["token"] == "firebase-token-123"
        assert data["platform"] == "android"
        assert "id" in data

    async def test_register_device_token_upsert(self, client, mock_verification_code):
        """Same token should update, not duplicate."""
        result = await register_user(client, VALID_EMAIL, COMPLETE_PROFILE_PAYLOAD, mock_verification_code)
        headers = {"Authorization": f"Bearer {result['access_token']}"}

        res1 = await client.post(
            DEVICE_TOKEN_URL,
            json={"token": "token-abc", "platform": "android"},
            headers=headers,
        )
        assert res1.status_code == 200
        id1 = res1.json()["id"]

        res2 = await client.post(
            DEVICE_TOKEN_URL,
            json={"token": "token-abc", "platform": "ios"},
            headers=headers,
        )
        assert res2.status_code == 200
        id2 = res2.json()["id"]
        # Same ID, updated platform
        assert id1 == id2
        assert res2.json()["platform"] == "ios"

    async def test_register_requires_auth(self, client):
        """Should require authentication."""
        res = await client.post(
            DEVICE_TOKEN_URL,
            json={"token": "token-xyz", "platform": "android"},
        )
        assert res.status_code == 401

    async def test_register_invalid_platform(self, client, mock_verification_code):
        """Should reject invalid platform."""
        result = await register_user(client, VALID_EMAIL, COMPLETE_PROFILE_PAYLOAD, mock_verification_code)
        headers = {"Authorization": f"Bearer {result['access_token']}"}

        res = await client.post(
            DEVICE_TOKEN_URL,
            json={"token": "token-xyz", "platform": "windows"},
            headers=headers,
        )
        assert res.status_code == 422

    async def test_delete_device_token(self, client, mock_verification_code):
        """Should delete a device token."""
        result = await register_user(client, VALID_EMAIL, COMPLETE_PROFILE_PAYLOAD, mock_verification_code)
        headers = {"Authorization": f"Bearer {result['access_token']}"}

        # Register token
        res = await client.post(
            DEVICE_TOKEN_URL,
            json={"token": "token-del", "platform": "android"},
            headers=headers,
        )
        assert res.status_code == 200
        token_id = res.json()["id"]

        # Delete token
        res = await client.delete(
            f"/api/v1/notifications/device-token/{token_id}",
            headers=headers,
        )
        assert res.status_code == 204

    async def test_delete_nonexistent_token_404(self, client, mock_verification_code):
        """Should return 404 for nonexistent token."""
        result = await register_user(client, VALID_EMAIL, COMPLETE_PROFILE_PAYLOAD, mock_verification_code)
        headers = {"Authorization": f"Bearer {result['access_token']}"}

        fake_id = str(uuid4())
        res = await client.delete(
            f"/api/v1/notifications/device-token/{fake_id}",
            headers=headers,
        )
        assert res.status_code == 404


class TestPushOnLike:

    @patch("app.services.push_service.PushService.send_to_user", new_callable=AsyncMock)
    async def test_push_sent_on_like(
        self, mock_send, client, mock_verification_code
    ):
        """Push notification should be sent when someone likes a user."""
        user1 = await register_user(client, VALID_EMAIL, COMPLETE_PROFILE_PAYLOAD, mock_verification_code)
        user2 = await register_user(client, VALID_EMAIL_2, COMPLETE_PROFILE_PAYLOAD_2, mock_verification_code)

        headers1 = {"Authorization": f"Bearer {user1['access_token']}"}
        user2_id = user2["user"]["id"]

        res = await client.post(
            SWIPE_URL,
            json={"user_id": user2_id, "direction": "like"},
            headers=headers1,
        )
        assert res.status_code == 200

        # Push should have been called for the liked user
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args.kwargs
        assert call_kwargs["user_id"].__str__() == user2_id
        assert "liked" in call_kwargs["title"].lower()


class TestPushOnMatch:

    @patch("app.services.push_service.PushService.send_to_user", new_callable=AsyncMock)
    async def test_push_sent_on_match(
        self, mock_send, client, mock_verification_code
    ):
        """Push notifications should be sent to both users on match."""
        user1 = await register_user(client, VALID_EMAIL, COMPLETE_PROFILE_PAYLOAD, mock_verification_code)
        user2 = await register_user(client, VALID_EMAIL_2, COMPLETE_PROFILE_PAYLOAD_2, mock_verification_code)

        headers1 = {"Authorization": f"Bearer {user1['access_token']}"}
        headers2 = {"Authorization": f"Bearer {user2['access_token']}"}
        user1_id = user1["user"]["id"]
        user2_id = user2["user"]["id"]

        # User 1 likes user 2
        await client.post(
            SWIPE_URL,
            json={"user_id": user2_id, "direction": "like"},
            headers=headers1,
        )
        # Reset to only count notifications from the second swipe
        mock_send.reset_mock()
        # User 2 likes user 1 (creates match)
        res = await client.post(
            SWIPE_URL,
            json={"user_id": user1_id, "direction": "like"},
            headers=headers2,
        )
        assert res.status_code == 200

        # Match notifications should have been sent to both users
        match_calls = [
            c for c in mock_send.call_args_list
            if c.kwargs.get("title") == "It's a match!"
        ]
        assert len(match_calls) == 2


class TestPushOnMessage:

    @patch("app.services.push_service.PushService.send_to_user", new_callable=AsyncMock)
    async def test_push_sent_on_message(
        self, mock_send, client, mock_verification_code
    ):
        """Push notification should be sent when a message is sent."""
        user1 = await register_user(client, VALID_EMAIL, COMPLETE_PROFILE_PAYLOAD, mock_verification_code)
        user2 = await register_user(client, VALID_EMAIL_2, COMPLETE_PROFILE_PAYLOAD_2, mock_verification_code)

        headers1 = {"Authorization": f"Bearer {user1['access_token']}"}
        headers2 = {"Authorization": f"Bearer {user2['access_token']}"}
        user1_id = user1["user"]["id"]
        user2_id = user2["user"]["id"]

        # Create match first
        await client.post(SWIPE_URL, json={"user_id": user2_id, "direction": "like"}, headers=headers1)
        await client.post(SWIPE_URL, json={"user_id": user1_id, "direction": "like"}, headers=headers2)

        # Get match_id
        matches_res = await client.get("/api/v1/matches", headers=headers1)
        assert matches_res.status_code == 200
        matches = matches_res.json()["matches"]
        assert len(matches) > 0
        match_id = matches[0]["id"]

        # Send message
        mock_send.reset_mock()
        res = await client.post(
            f"/api/v1/messages/{match_id}/text",
            json={"content": "Hello!"},
            headers=headers1,
        )
        assert res.status_code == 200

        # Push should have been called for the receiver
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args.kwargs
        assert call_kwargs["user_id"].__str__() == user2_id
