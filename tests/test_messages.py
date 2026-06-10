import pytest
from httpx import AsyncClient
from uuid import uuid4

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
SWIPE_URL = "/api/v1/swipes"
MESSAGES_URL = "/api/v1/messages"

VALID_REGISTER_PAYLOAD_MALE = {
    "email": "chat_male@example.com",
    "password": "strongpass123",
    "name": "Chat Male",
    "age": 25,
    "gender": "male",
}

VALID_REGISTER_PAYLOAD_FEMALE = {
    "email": "chat_female@example.com",
    "password": "strongpass123",
    "name": "Chat Female",
    "age": 24,
    "gender": "female",
}


async def register_and_get_headers(client: AsyncClient, payload: dict) -> tuple[dict, str]:
    reg_res = await client.post(REGISTER_URL, json=payload)
    assert reg_res.status_code == 201
    data = reg_res.json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    user_id = data["user"]["id"]
    return headers, user_id


class TestMessages:
    
    async def test_send_text_message_in_matched_chat(self, client: AsyncClient):
        """Should send text message in matched chat"""
        male_headers, male_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)

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

    async def test_get_chat_history(self, client: AsyncClient):
        """Should get chat history"""
        male_headers, male_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)

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

    async def test_unmatched_chat_limit(self, client: AsyncClient):
        """Should enforce 2 message limit in unmatched chat"""
        male_headers, male_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)

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

    async def test_accept_chat(self, client: AsyncClient):
        """Should accept unmatched chat"""
        male_headers, male_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)

        await client.post(SWIPE_URL, json={"user_id": female_id, "direction": "like"}, headers=male_headers)

        # Send two messages (male to female)
        await client.post(f"{MESSAGES_URL}/{female_id}/text", json={"content": "Hi"}, headers=male_headers)
        await client.post(f"{MESSAGES_URL}/{female_id}/text", json={"content": "How are you?"}, headers=male_headers)

        # Accept chat - female accepts the chat from male, so identifier should be male_id
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

    async def test_delete_message_for_me(self, client: AsyncClient):
        """Should delete message for me"""
        male_headers, male_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)

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

    async def test_mark_messages_as_read(self, client: AsyncClient):
        """Should mark messages as read"""
        male_headers, male_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)

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