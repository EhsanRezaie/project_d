import pytest
from httpx import AsyncClient

REGISTER_URL = "/api/v1/auth/register"
BLOCKS_URL = "/api/v1/blocks"
SEARCH_URL = "/api/v1/search"

VALID_REGISTER_PAYLOAD_MALE = {
    "email": "block_male@example.com",
    "password": "strongpass123",
    "name": "Block Male",
    "age": 25,
    "gender": "male",
}

VALID_REGISTER_PAYLOAD_FEMALE = {
    "email": "block_female@example.com",
    "password": "strongpass123",
    "name": "Block Female",
    "age": 24,
    "gender": "female",
}

VALID_REGISTER_PAYLOAD_FEMALE2 = {
    "email": "block_female2@example.com",
    "password": "strongpass123",
    "name": "Block Female 2",
    "age": 26,
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


class TestBlocks:
    
    async def test_block_user_success(self, client: AsyncClient):
        """Should block a user successfully"""
        male_headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        res = await client.post(f"{BLOCKS_URL}/{female_id}/block", headers=male_headers)
        assert res.status_code == 204
    
    async def test_block_self_fails(self, client: AsyncClient):
        """Cannot block yourself"""
        headers, user_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        
        res = await client.post(f"{BLOCKS_URL}/{user_id}/block", headers=headers)
        assert res.status_code == 400
        assert "Cannot block yourself" in res.json()["detail"]
    
    async def test_block_nonexistent_user_fails(self, client: AsyncClient):
        """Cannot block non-existent user"""
        headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        
        res = await client.post(
            f"{BLOCKS_URL}/00000000-0000-0000-0000-000000000000/block", 
            headers=headers
        )
        assert res.status_code == 404
        assert "User not found" in res.json()["detail"]
    
    async def test_block_twice_fails(self, client: AsyncClient):
        """Cannot block same user twice"""
        male_headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        # First block
        res1 = await client.post(f"{BLOCKS_URL}/{female_id}/block", headers=male_headers)
        assert res1.status_code == 204
        
        # Second block - should fail
        res2 = await client.post(f"{BLOCKS_URL}/{female_id}/block", headers=male_headers)
        assert res2.status_code == 400
        assert "already blocked" in res2.json()["detail"].lower()
    
    async def test_unblock_user_success(self, client: AsyncClient):
        """Should unblock a user successfully"""
        male_headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        # Block first
        await client.post(f"{BLOCKS_URL}/{female_id}/block", headers=male_headers)
        
        # Then unblock
        res = await client.post(f"{BLOCKS_URL}/{female_id}/unblock", headers=male_headers)
        assert res.status_code == 204
    
    async def test_unblock_not_blocked_fails(self, client: AsyncClient):
        """Cannot unblock a user that wasn't blocked"""
        male_headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        res = await client.post(f"{BLOCKS_URL}/{female_id}/unblock", headers=male_headers)
        assert res.status_code == 404
        assert "Block not found" in res.json()["detail"]
    
    async def test_list_blocks_empty(self, client: AsyncClient):
        """Should return empty list when no blocks"""
        headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        
        res = await client.get(BLOCKS_URL, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    async def test_list_blocks_with_blocks(self, client: AsyncClient):
        """Should return list of blocked users"""
        male_headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        female2_headers, female2_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE2)
        
        # Block two users
        await client.post(f"{BLOCKS_URL}/{female_id}/block", headers=male_headers)
        await client.post(f"{BLOCKS_URL}/{female2_id}/block", headers=male_headers)
        
        res = await client.get(BLOCKS_URL, headers=male_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 2
        
        # Check response structure
        for block in data:
            assert "id" in block
            assert "blocked_user_id" in block
            assert "blocked_user_name" in block
            assert "blocked_at" in block
    
    async def test_blocked_user_not_in_search(self, client: AsyncClient):
        """Blocked users should not appear in search results"""
        male_headers, _ = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_MALE)
        female_headers, female_id = await register_and_get_headers(client, VALID_REGISTER_PAYLOAD_FEMALE)
        
        # Search before block - should see female
        res_before = await client.get(SEARCH_URL, headers=male_headers)
        assert res_before.status_code == 200
        users_before = [u["id"] for u in res_before.json()["users"]]
        
        # Block female
        await client.post(f"{BLOCKS_URL}/{female_id}/block", headers=male_headers)
        
        # Search after block - should NOT see female
        res_after = await client.get(SEARCH_URL, headers=male_headers)
        assert res_after.status_code == 200
        users_after = [u["id"] for u in res_after.json()["users"]]
        
        assert female_id in users_before
        assert female_id not in users_after
    
    async def test_block_requires_auth(self, client: AsyncClient):
        """Block endpoint requires authentication"""
        res = await client.post(f"{BLOCKS_URL}/123/block")
        assert res.status_code == 401
    
    async def test_unblock_requires_auth(self, client: AsyncClient):
        """Unblock endpoint requires authentication"""
        res = await client.post(f"{BLOCKS_URL}/123/unblock")
        assert res.status_code == 401
    
    async def test_list_blocks_requires_auth(self, client: AsyncClient):
        """List blocks endpoint requires authentication"""
        res = await client.get(BLOCKS_URL)
        assert res.status_code == 401