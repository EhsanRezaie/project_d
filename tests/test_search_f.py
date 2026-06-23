import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

REGISTER_URL = "/api/v1/auth/register"
SEARCH_URL = "/api/v1/search"
BLOCKS_URL = "/api/v1/blocks"

VALID_REGISTER_PAYLOAD_MALE = {
    "email": "search_male@example.com",
    "password": "strongpass123",
    "name": "Search Male",
    "age": 25,
    "gender": "male",
    "height": 180,
    "weight": 75,
}

VALID_REGISTER_PAYLOAD_FEMALE = {
    "email": "search_female@example.com",
    "password": "strongpass123",
    "name": "Search Female",
    "age": 24,
    "gender": "female",
    "height": 165,
    "weight": 60,
}


async def register_and_get_headers(client: AsyncClient, payload: dict) -> tuple[dict, str]:
    reg_res = await client.post(REGISTER_URL, json=payload)
    assert reg_res.status_code == 201
    data = reg_res.json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    user_id = data["user"]["id"]
    return headers, user_id


class TestSearch:
    
    async def test_search_returns_users(self, client: AsyncClient):
        """Should return users"""
        headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        res = await client.get(SEARCH_URL, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "users" in data
        assert "total" in data
    
    async def test_search_age_filter(self, client: AsyncClient):
        """Should filter by age"""
        headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        
        res = await client.get(
            SEARCH_URL,
            params={"age_min": 30, "age_max": 40},
            headers=headers,
        )
        assert res.status_code == 200
    
    async def test_search_gender_filter(self, client: AsyncClient):
        """Should filter by gender"""
        headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        res = await client.get(
            SEARCH_URL,
            params={"gender": "female"},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        
        for user in data["users"]:
            assert user["gender"] == "female"
    
    async def test_search_height_filter(self, client: AsyncClient):
        """Should filter by height"""
        headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        
        res = await client.get(
            SEARCH_URL,
            params={"height_min": 170, "height_max": 190},
            headers=headers,
        )
        assert res.status_code == 200
    
    async def test_search_country_filter(self, client: AsyncClient):
        """Should filter by country"""
        headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        
        res = await client.get(
            SEARCH_URL,
            params={"country": "Iran"},
            headers=headers,
        )
        assert res.status_code == 200
    
    async def test_search_province_filter(self, client: AsyncClient):
        """Should filter by province"""
        headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        
        res = await client.get(
            SEARCH_URL,
            params={"province": "Tehran"},
            headers=headers,
        )
        assert res.status_code == 200
    
    async def test_search_city_filter(self, client: AsyncClient):
        """Should filter by city"""
        headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        
        res = await client.get(
            SEARCH_URL,
            params={"city": "Shiraz"},
            headers=headers,
        )
        assert res.status_code == 200
    
    async def test_search_combined_location_filters(self, client: AsyncClient):
        """Should filter by country, province, and city together"""
        headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        
        res = await client.get(
            SEARCH_URL,
            params={"country": "Iran", "province": "Tehran", "city": "Tehran"},
            headers=headers,
        )
        assert res.status_code == 200
    
    async def test_search_distance_filter(self, client: AsyncClient):
        """Should filter by distance"""
        headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        
        # First set current user's location
        await client.post(
            "/api/v1/users/me/location",
            params={"lat": 35.6892, "lng": 51.3890},
            headers=headers
        )
        
        res = await client.get(
            SEARCH_URL,
            params={"distance_km": 50},
            headers=headers,
        )
        assert res.status_code == 200
    
    async def test_search_requires_auth(self, client: AsyncClient):
        """Should return 401 without token"""
        res = await client.get(SEARCH_URL)
        assert res.status_code == 401


class TestBlocks:
    
    async def test_block_user_success(self, client: AsyncClient):
        """Should block a user"""
        headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        _, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        res = await client.post(f"{BLOCKS_URL}/{female_id}/block", headers=headers)
        assert res.status_code == 204
    
    async def test_block_self_fails(self, client: AsyncClient):
        """Cannot block yourself"""
        headers, user_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        
        res = await client.post(f"{BLOCKS_URL}/{user_id}/block", headers=headers)
        assert res.status_code == 400
    
    async def test_unblock_user_success(self, client: AsyncClient):
        """Should unblock a user"""
        headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        _, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        await client.post(f"{BLOCKS_URL}/{female_id}/block", headers=headers)
        res = await client.post(f"{BLOCKS_URL}/{female_id}/unblock", headers=headers)
        assert res.status_code == 204
    
    async def test_list_blocks(self, client: AsyncClient):
        """Should list blocked users"""
        headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        _, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        await client.post(f"{BLOCKS_URL}/{female_id}/block", headers=headers)
        
        res = await client.get(BLOCKS_URL, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
    
    async def test_blocked_user_not_in_search(self, client: AsyncClient):
        """Blocked user should not appear in search results"""
        # Create blocker
        blocker_headers, blocker_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        
        # Create user to block
        user_to_block_payload = {
            "email": "to_block@example.com",
            "password": "strongpass123",
            "name": "To Block",
            "age": 25,
            "gender": "female"
        }
        block_user_res = await client.post("/api/v1/auth/register", json=user_to_block_payload)
        block_user_id = block_user_res.json()["user"]["id"]
        
        # Block the user
        await client.post(f"{BLOCKS_URL}/{block_user_id}/block", headers=blocker_headers)
        
        # Search should not return blocked user
        search_res = await client.get(SEARCH_URL, headers=blocker_headers)
        assert search_res.status_code == 200
        users = search_res.json().get("users", [])
        
        blocked_found = any(u.get("id") == block_user_id for u in users)
        assert blocked_found is False