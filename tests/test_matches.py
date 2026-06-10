import pytest
from httpx import AsyncClient

REGISTER_URL = "/api/v1/auth/register"
SWIPE_URL = "/api/v1/swipes"
MATCHES_URL = "/api/v1/matches"

VALID_REGISTER_PAYLOAD_MALE = {
    "email": "match_male@example.com",
    "password": "strongpass123",
    "name": "Match Male",
    "age": 25,
    "gender": "male",
}

VALID_REGISTER_PAYLOAD_FEMALE = {
    "email": "match_female@example.com",
    "password": "strongpass123",
    "name": "Match Female",
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


class TestMatches:
    
    async def test_get_matches_empty(self, client: AsyncClient):
        """Should return empty list when no matches"""
        headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        
        res = await client.get(MATCHES_URL, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["matches"] == []
        assert data["total"] == 0
    
    async def test_get_matches_after_match(self, client: AsyncClient):
        """Should return matches after mutual like"""
        male_headers, male_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        # Male likes female
        await client.post(
            SWIPE_URL,
            json={"user_id": female_id, "direction": "like"},
            headers=male_headers,
        )
        
        # Female likes male (creates match)
        await client.post(
            SWIPE_URL,
            json={"user_id": male_id, "direction": "like"},
            headers=female_headers,
        )
        
        # Check matches for male
        res = await client.get(MATCHES_URL, headers=male_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        
        # Check match structure
        match = data["matches"][0]
        assert "id" in match
        assert "matched_at" in match
        assert "user" in match
        assert "id" in match["user"]
        assert "name" in match["user"]
        assert "age" in match["user"]
    
    async def test_get_match_detail(self, client: AsyncClient):
        """Should return match details"""
        male_headers, male_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        # Create match
        await client.post(
            SWIPE_URL,
            json={"user_id": female_id, "direction": "like"},
            headers=male_headers,
        )
        
        match_res = await client.post(
            SWIPE_URL,
            json={"user_id": male_id, "direction": "like"},
            headers=female_headers,
        )
        match_data = match_res.json()
        match_id = match_data["match_id"]
        
        # Get match detail
        res = await client.get(f"{MATCHES_URL}/{match_id}", headers=male_headers)
        assert res.status_code == 200
        data = res.json()
        
        assert data["id"] == match_id
        assert "user1" in data
        assert "user2" in data
        assert "matched_at" in data
        assert data["is_active"] == True
    
    async def test_get_match_detail_unauthorized(self, client: AsyncClient):
        """Should not allow access to other user's match"""
        male_headers, male_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        # Create match
        await client.post(
            SWIPE_URL,
            json={"user_id": female_id, "direction": "like"},
            headers=male_headers,
        )
        
        match_res = await client.post(
            SWIPE_URL,
            json={"user_id": male_id, "direction": "like"},
            headers=female_headers,
        )
        match_id = match_res.json()["match_id"]
        
        # Register third user
        third_payload = {
            "email": "third@example.com",
            "password": "strongpass123",
            "name": "Third User",
            "age": 25,
            "gender": "male",
        }
        third_headers, _ = await register_and_get_headers(client, third_payload)
        
        # Third user trying to access match
        res = await client.get(f"{MATCHES_URL}/{match_id}", headers=third_headers)
        assert res.status_code == 404
    
    async def test_get_matches_requires_auth(self, client: AsyncClient):
        """Should return 401 without token"""
        res = await client.get(MATCHES_URL)
        assert res.status_code == 401