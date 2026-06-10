import pytest
from httpx import AsyncClient

REGISTER_URL = "/api/v1/auth/register"
SWIPE_URL = "/api/v1/swipes"

VALID_REGISTER_PAYLOAD_MALE = {
    "email": "swipe_male@example.com",
    "password": "strongpass123",
    "name": "Swipe Male",
    "age": 25,
    "gender": "male",
}

VALID_REGISTER_PAYLOAD_FEMALE = {
    "email": "swipe_female@example.com",
    "password": "strongpass123",
    "name": "Swipe Female",
    "age": 24,
    "gender": "female",
}


async def register_and_get_headers(client: AsyncClient, payload: dict) -> tuple[dict, str]:
    """Register user and return (headers, user_id)."""
    reg_res = await client.post(REGISTER_URL, json=payload)
    assert reg_res.status_code == 201
    data = reg_res.json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    user_id = data["user"]["id"]
    return headers, user_id


class TestSwipes:
    
    async def test_swipe_like_success(self, client: AsyncClient):
        """Should successfully like a user"""
        male_headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        res = await client.post(
            SWIPE_URL,
            json={"user_id": female_id, "direction": "like"},
            headers=male_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["matched"] is False
    
    async def test_swipe_pass_success(self, client: AsyncClient):
        """Should successfully pass on a user"""
        male_headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        res = await client.post(
            SWIPE_URL,
            json={"user_id": female_id, "direction": "pass"},
            headers=male_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["matched"] is False
    
    async def test_swipe_create_match(self, client: AsyncClient):
        """Should create match when both users like each other"""
        male_headers, male_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        # Male likes female
        await client.post(
            SWIPE_URL,
            json={"user_id": female_id, "direction": "like"},
            headers=male_headers,
        )
        
        # Female likes male (mutual)
        res = await client.post(
            SWIPE_URL,
            json={"user_id": male_id, "direction": "like"},
            headers=female_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["matched"] is True
        assert data["match_id"] is not None
    
    async def test_swipe_cannot_swipe_self(self, client: AsyncClient):
        """Should not allow swiping on yourself"""
        headers, user_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        
        res = await client.post(
            SWIPE_URL,
            json={"user_id": user_id, "direction": "like"},
            headers=headers,
        )
        assert res.status_code == 400
        assert "Cannot swipe on yourself" in res.json()["detail"]
    
    async def test_swipe_cannot_swipe_twice(self, client: AsyncClient):
        """Should not allow swiping on same user twice"""
        male_headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        # First swipe
        await client.post(
            SWIPE_URL,
            json={"user_id": female_id, "direction": "like"},
            headers=male_headers,
        )
        
        # Second swipe - should fail
        res = await client.post(
            SWIPE_URL,
            json={"user_id": female_id, "direction": "pass"},
            headers=male_headers,
        )
        assert res.status_code == 400
        assert "Already swiped" in res.json()["detail"]
    
    async def test_swipe_requires_auth(self, client: AsyncClient):
        """Should return 401 without token"""
        res = await client.post(SWIPE_URL, json={"user_id": "123", "direction": "like"})
        assert res.status_code == 401
    
    async def test_swipe_stats(self, client: AsyncClient):
        """Should return swipe statistics"""
        headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        
        res = await client.get(f"{SWIPE_URL}/stats", headers=headers)
        assert res.status_code == 200
        data = res.json()
        
        assert "daily_likes_remaining" in data
        assert "total_likes_sent" in data
        assert "total_passes_sent" in data
        assert "total_matches" in data