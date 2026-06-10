import pytest
from httpx import AsyncClient

REGISTER_URL = "/api/v1/auth/register"
DISCOVER_URL = "/api/v1/discover"
SWIPE_URL = "/api/v1/swipes"

VALID_REGISTER_PAYLOAD_MALE = {
    "email": "test_male@example.com",
    "password": "strongpass123",
    "name": "Male User",
    "age": 25,
    "gender": "male",
}

VALID_REGISTER_PAYLOAD_FEMALE = {
    "email": "test_female@example.com",
    "password": "strongpass123",
    "name": "Female User",
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


class TestDiscover:
    
    async def test_discover_returns_opposite_gender(self, client: AsyncClient):
        """Should only return opposite gender users"""
        male_headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        res = await client.get(DISCOVER_URL, headers=male_headers)
        assert res.status_code == 200
        data = res.json()
        
        for user in data["users"]:
            assert user["gender"] == "female"
    
    async def test_discover_excludes_swiped_users(self, client: AsyncClient):
        """Should exclude users already swiped on"""
        male_headers, male_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        # Male swipes on female
        await client.post(
            SWIPE_URL,
            json={"user_id": female_id, "direction": "like"},
            headers=male_headers,
        )
        
        # Discover should NOT show female
        res = await client.get(DISCOVER_URL, headers=male_headers)
        assert res.status_code == 200
        data = res.json()
        
        female_ids = [u["id"] for u in data["users"]]
        assert female_id not in female_ids
    
    async def test_discover_requires_auth(self, client: AsyncClient):
        """Should return 401 without token"""
        res = await client.get(DISCOVER_URL)
        assert res.status_code == 401
    
    async def test_discover_age_filter(self, client: AsyncClient):
        """Should filter by age range"""
        male_headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        
        # Register female with age 25
        female_payload = {
            "email": "female_age25@example.com",
            "password": "strongpass123",
            "name": "Female 25",
            "age": 25,
            "gender": "female",
        }
        await register_and_get_headers(client, female_payload)
        
        # Search for age 30-40 - should return none
        res = await client.get(
            DISCOVER_URL,
            params={"age_min": 30, "age_max": 40},
            headers=male_headers,
        )
        assert res.status_code == 200
    
    async def test_discover_pagination(self, client: AsyncClient):
        """Should support pagination"""
        male_headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        
        # Register 3 female users
        for i in range(3):
            female_payload = {
                "email": f"pagination_{i}@example.com",
                "password": "strongpass123",
                "name": f"Pagination {i}",
                "age": 20 + i,
                "gender": "female",
            }
            await register_and_get_headers(client, female_payload)
        
        res1 = await client.get(DISCOVER_URL, params={"limit": 2, "offset": 0}, headers=male_headers)
        assert res1.status_code == 200