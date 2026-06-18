import pytest
from httpx import AsyncClient

REGISTER_INIT_URL = "/api/v1/auth/register/init"
REGISTER_VERIFY_URL = "/api/v1/auth/register/verify"
REGISTER_COMPLETE_URL = "/api/v1/auth/register/complete"
LOGIN_URL = "/api/v1/auth/login"
USERS_ME_URL = "/api/v1/users/me"
USERS_ME_LOCATION_URL = "/api/v1/users/me/location"
USERS_ME_LOCATION_TEXT_URL = "/api/v1/users/me/location-text"

VALID_EMAIL = "test@example.com"
VALID_PASSWORD = "strongpass123"
VALID_CODE = "123456"

COMPLETE_PROFILE_PAYLOAD = {
    "name": "Test User",
    "birth_date": "1995-06-15",
    "gender": "male",
    "height": 180,
    "weight": 75,
    "lat": 35.6892,
    "lng": 51.3890,
    "country": "Iran",
    "province": "Tehran",
    "city": "Tehran",
}


async def register_and_login(client: AsyncClient) -> tuple[dict, dict]:
    """Helper: complete full registration and return (token_data, headers)."""
    # Step 1: Init
    await client.post(REGISTER_INIT_URL, json={"email": VALID_EMAIL})
    
    # Step 2: Verify
    verify_res = await client.post(REGISTER_VERIFY_URL, json={
        "email": VALID_EMAIL,
        "code": VALID_CODE,
        "password": VALID_PASSWORD,
    })
    data = verify_res.json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    
    # Step 3: Complete profile
    res = await client.post(REGISTER_COMPLETE_URL, json=COMPLETE_PROFILE_PAYLOAD, headers=headers)
    assert res.status_code == 200
    token_data = res.json()
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    
    return token_data, headers


# ---------------------------------------------------------------------------
# GET /api/v1/users/me
# ---------------------------------------------------------------------------

class TestGetMe:
    
    async def test_get_me_success(self, client: AsyncClient):
        """Should return current user profile with all fields."""
        _, headers = await register_and_login(client)
        
        res = await client.get(USERS_ME_URL, headers=headers)
        assert res.status_code == 200
        data = res.json()
        
        assert data["email"] == VALID_EMAIL
        assert data["name"] == "Test User"
        assert data["age"] == 29  # 1995-06-15 to 2024
        assert data["gender"] == "male"
        assert data["height"] == 180
        assert data["weight"] == 75
        assert data["country"] == "Iran"
        assert data["province"] == "Tehran"
        assert data["city"] == "Tehran"
        assert data["is_profile_complete"] is True
        assert "password_hash" not in data
    
    async def test_get_me_requires_auth(self, client: AsyncClient):
        """Should return 401 without token."""
        res = await client.get(USERS_ME_URL)
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
    
    async def test_update_body_type_success(self, client: AsyncClient):
        """Should update body type."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={"body_type": "athletic"},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["body_type"] == "athletic"
    
    async def test_update_relationship_status_success(self, client: AsyncClient):
        """Should update relationship status."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={"relationship_status": "single"},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["relationship_status"] == "single"
    
    async def test_update_education_success(self, client: AsyncClient):
        """Should update education."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={"education": "master"},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["education"] == "master"
    
    async def test_update_workplace_success(self, client: AsyncClient):
        """Should update workplace."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={"workplace": "Google"},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["workplace"] == "Google"
    
    async def test_update_height_weight_success(self, client: AsyncClient):
        """Should update height and weight."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={"height": 175, "weight": 70},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["height"] == 175
        assert data["weight"] == 70
    
    async def test_update_multiple_fields_success(self, client: AsyncClient):
        """Should update multiple fields at once."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={
                "name": "Updated Name",
                "bio": "Updated bio",
                "gender": "female",
                "height": 170,
                "weight": 60,
                "body_type": "slim",
                "relationship_status": "divorced",
                "education": "phd",
                "workplace": "Microsoft",
            },
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "Updated Name"
        assert data["bio"] == "Updated bio"
        assert data["gender"] == "female"
        assert data["height"] == 170
        assert data["weight"] == 60
        assert data["body_type"] == "slim"
        assert data["relationship_status"] == "divorced"
        assert data["education"] == "phd"
        assert data["workplace"] == "Microsoft"
    
    async def test_update_invalid_gender(self, client: AsyncClient):
        """Should reject invalid gender."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={"gender": "invalid"},
            headers=headers,
        )
        assert res.status_code == 422
    
    async def test_update_invalid_body_type(self, client: AsyncClient):
        """Should reject invalid body type."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={"body_type": "invalid"},
            headers=headers,
        )
        assert res.status_code == 422
    
    async def test_update_invalid_relationship_status(self, client: AsyncClient):
        """Should reject invalid relationship status."""
        _, headers = await register_and_login(client)
        
        res = await client.put(
            USERS_ME_URL,
            json={"relationship_status": "invalid"},
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
        
        login_res = await client.post(LOGIN_URL, json={
            "email": VALID_EMAIL,
            "password": VALID_PASSWORD,
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
        """Should update user location with lat/lng."""
        _, headers = await register_and_login(client)
        
        res = await client.post(
            USERS_ME_LOCATION_URL,
            params={"lat": 35.6892, "lng": 51.3890},
            headers=headers,
        )
        assert res.status_code == 204
        
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
    
    async def test_update_location_requires_auth(self, client: AsyncClient):
        """Should return 401 without token."""
        res = await client.post(
            USERS_ME_LOCATION_URL,
            params={"lat": 35.6892, "lng": 51.3890},
        )
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /api/v1/users/me/location-text
# ---------------------------------------------------------------------------

class TestUpdateLocationText:
    
    async def test_update_location_text_success(self, client: AsyncClient):
        """Should update location with text fields."""
        _, headers = await register_and_login(client)
        
        res = await client.patch(
            USERS_ME_LOCATION_TEXT_URL,
            json={
                "country": "Iran",
                "province": "Isfahan",
                "city": "Isfahan"
            },
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["country"] == "Iran"
        assert data["province"] == "Isfahan"
        assert data["city"] == "Isfahan"
        assert data["location_manual"] is True
    
    async def test_update_location_text_requires_auth(self, client: AsyncClient):
        """Should return 401 without token."""
        res = await client.patch(
            USERS_ME_LOCATION_TEXT_URL,
            json={"country": "Iran", "province": "Tehran", "city": "Tehran"}
        )
        assert res.status_code == 401