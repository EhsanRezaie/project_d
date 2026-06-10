import pytest
from httpx import AsyncClient

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
USERS_ME_URL = "/api/v1/users/me"
USERS_ME_LOCATION_URL = "/api/v1/users/me/location"

VALID_REGISTER_PAYLOAD = {
    "email": "test@example.com",
    "password": "strongpass123",
    "name": "Test User",
    "age": 25,
    "gender": "male",
}


async def register_and_login(client: AsyncClient) -> tuple[dict, dict]:
    """Helper: register user and return (user_data, auth_headers)."""
    reg_res = await client.post(REGISTER_URL, json=VALID_REGISTER_PAYLOAD)
    assert reg_res.status_code == 201
    data = reg_res.json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    return data, headers


# ---------------------------------------------------------------------------
# GET /api/v1/users/me
# ---------------------------------------------------------------------------

class TestGetMe:
    
    async def test_get_me_success(self, client: AsyncClient):
        """Should return current user profile."""
        _, headers = await register_and_login(client)
        
        res = await client.get(USERS_ME_URL, headers=headers)
        assert res.status_code == 200
        data = res.json()
        
        assert data["email"] == VALID_REGISTER_PAYLOAD["email"]
        assert data["name"] == VALID_REGISTER_PAYLOAD["name"]
        assert data["age"] == VALID_REGISTER_PAYLOAD["age"]
        assert data["gender"] == VALID_REGISTER_PAYLOAD["gender"]
        assert "password_hash" not in data
        assert "google_id" not in data
    
    async def test_get_me_requires_auth(self, client: AsyncClient):
        """Should return 401 without token."""
        res = await client.get(USERS_ME_URL)
        assert res.status_code == 401
    
    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Should return 401 with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        res = await client.get(USERS_ME_URL, headers=headers)
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# PUT /api/v1/users/me
# ---------------------------------------------------------------------------

class TestUpdateMe:
    
    async def test_update_name_success(self, client: AsyncClient):
        """Should update user name."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={"name": "New Name"},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "New Name"
    
    async def test_update_bio_success(self, client: AsyncClient):
        """Should update user bio."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={"bio": "This is my bio"},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["bio"] == "This is my bio"
    
    async def test_update_age_success(self, client: AsyncClient):
        """Should update user age."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={"age": 30},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["age"] == 30
    
    async def test_update_height_weight_success(self, client: AsyncClient):
        """Should update height and weight."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={"height": 180, "weight": 75},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["height"] == 180
        assert data["weight"] == 75
    
    async def test_update_multiple_fields_success(self, client: AsyncClient):
        """Should update multiple fields at once."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={
                "name": "Updated Name",
                "bio": "Updated bio",
                "age": 28,
                "gender": "female",
                "height": 175,
                "weight": 65,
            },
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "Updated Name"
        assert data["bio"] == "Updated bio"
        assert data["age"] == 28
        assert data["gender"] == "female"
        assert data["height"] == 175
        assert data["weight"] == 65
    
    async def test_update_invalid_age(self, client: AsyncClient):
        """Should reject age under 18."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={"age": 15},
            headers=headers,
        )
        assert res.status_code == 422
    
    async def test_update_invalid_gender(self, client: AsyncClient):
        """Should reject invalid gender."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={"gender": "invalid"},
            headers=headers,
        )
        assert res.status_code == 422
    
    async def test_update_invalid_height(self, client: AsyncClient):
        """Should reject height outside range."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={"height": 300},
            headers=headers,
        )
        assert res.status_code == 422
    
    async def test_update_invalid_weight(self, client: AsyncClient):
        """Should reject weight outside range."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={"weight": 10},
            headers=headers,
        )
        assert res.status_code == 422
    
    async def test_update_empty_body(self, client: AsyncClient):
        """Should reject empty update."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={},
            headers=headers,
        )
        assert res.status_code == 400
        assert "No fields to update" in res.json()["detail"]
    
    async def test_update_requires_auth(self, client: AsyncClient):
        """Should return 401 without token."""
        res = await client.put(USERS_ME_URL, json={"name": "New Name"})
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /api/v1/users/me
# ---------------------------------------------------------------------------

class TestDeleteMe:
    
    async def test_delete_me_success(self, client: AsyncClient):
        """Should soft delete user account."""
        _, headers = await register_and_login(client)
        
        res = await client.delete(USERS_ME_URL, headers=headers)
        assert res.status_code == 204
        
        # Try to login again - should fail
        login_res = await client.post(LOGIN_URL, json={
            "email": VALID_REGISTER_PAYLOAD["email"],
            "password": VALID_REGISTER_PAYLOAD["password"],
        })
        assert login_res.status_code == 401
    
    async def test_delete_me_requires_auth(self, client: AsyncClient):
        """Should return 401 without token."""
        res = await client.delete(USERS_ME_URL)
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/v1/users/me/location
# ---------------------------------------------------------------------------

class TestUpdateLocation:
    
    async def test_update_location_success(self, client: AsyncClient):
        """Should update user location."""
        _, headers = await register_and_login(client)
        
        res = await client.post(
            USERS_ME_LOCATION_URL,
            params={"lat": 35.6892, "lng": 51.3890},
            headers=headers,
        )
        assert res.status_code == 204
        
        # Verify location was saved
        get_res = await client.get(USERS_ME_URL, headers=headers)
        assert get_res.status_code == 200
        data = get_res.json()
        assert data["lat"] == 35.6892
        assert data["lng"] == 51.3890
    
    async def test_update_location_invalid_lat(self, client: AsyncClient):
        """Should reject invalid latitude."""
        _, headers = await register_and_login(client)
        
        res = await client.post(
            USERS_ME_LOCATION_URL,
            params={"lat": 100, "lng": 51.3890},
            headers=headers,
        )
        assert res.status_code == 400
    
    async def test_update_location_invalid_lng(self, client: AsyncClient):
        """Should reject invalid longitude."""
        _, headers = await register_and_login(client)
        
        res = await client.post(
            USERS_ME_LOCATION_URL,
            params={"lat": 35.6892, "lng": 200},
            headers=headers,
        )
        assert res.status_code == 400
    
    async def test_update_location_requires_auth(self, client: AsyncClient):
        """Should return 401 without token."""
        res = await client.post(
            USERS_ME_LOCATION_URL,
            params={"lat": 35.6892, "lng": 51.3890},
        )
        assert res.status_code == 401