import pytest
from httpx import AsyncClient
from jose import jwt

from app.core.config import settings
from app.models.user import User

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"
COMPLETE_PROFILE_URL = "/api/v1/auth/complete-profile"
CHANGE_PASSWORD_URL = "/api/v1/auth/change-password"
HEALTH_URL = "/api/v1/auth/health"

VALID_REGISTER_PAYLOAD = {
    "email": "test@example.com",
    "password": "strongpass123",
    "name": "Test User",
    "age": 25,
    "gender": "male",
}


async def register_user(client: AsyncClient, payload: dict = None) -> dict:
    """Helper — register a user and return the full JSON response."""
    payload = payload or VALID_REGISTER_PAYLOAD
    res = await client.post(REGISTER_URL, json=payload)
    assert res.status_code == 201, res.text
    return res.json()


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------

class TestRegister:

    async def test_register_success(self, client: AsyncClient):
        res = await client.post(REGISTER_URL, json=VALID_REGISTER_PAYLOAD)
        assert res.status_code == 201
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == VALID_REGISTER_PAYLOAD["email"]
        assert data["user"]["is_profile_complete"] is True

    async def test_register_duplicate_email(self, client: AsyncClient):
        await register_user(client)
        res = await client.post(REGISTER_URL, json=VALID_REGISTER_PAYLOAD)
        assert res.status_code == 409
        assert "already exists" in res.json()["detail"]

    async def test_register_invalid_email(self, client: AsyncClient):
        payload = {**VALID_REGISTER_PAYLOAD, "email": "not-an-email"}
        res = await client.post(REGISTER_URL, json=payload)
        assert res.status_code == 422

    async def test_register_password_too_short(self, client: AsyncClient):
        payload = {**VALID_REGISTER_PAYLOAD, "password": "short"}
        res = await client.post(REGISTER_URL, json=payload)
        assert res.status_code == 422

    async def test_register_invalid_gender(self, client: AsyncClient):
        payload = {**VALID_REGISTER_PAYLOAD, "gender": "attack_helicopter"}
        res = await client.post(REGISTER_URL, json=payload)
        assert res.status_code == 422

    async def test_register_underage(self, client: AsyncClient):
        payload = {**VALID_REGISTER_PAYLOAD, "age": 17}
        res = await client.post(REGISTER_URL, json=payload)
        assert res.status_code == 422

    async def test_register_whitespace_password(self, client: AsyncClient):
        payload = {**VALID_REGISTER_PAYLOAD, "password": "        "}
        res = await client.post(REGISTER_URL, json=payload)
        assert res.status_code == 422


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

class TestLogin:

    async def test_login_success(self, client: AsyncClient):
        await register_user(client)
        res = await client.post(LOGIN_URL, json={
            "email": VALID_REGISTER_PAYLOAD["email"],
            "password": VALID_REGISTER_PAYLOAD["password"],
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(self, client: AsyncClient):
        await register_user(client)
        res = await client.post(LOGIN_URL, json={
            "email": VALID_REGISTER_PAYLOAD["email"],
            "password": "wrongpassword",
        })
        assert res.status_code == 401
        assert "Incorrect" in res.json()["detail"]

    async def test_login_nonexistent_email(self, client: AsyncClient):
        res = await client.post(LOGIN_URL, json={
            "email": "nobody@example.com",
            "password": "somepassword",
        })
        assert res.status_code == 401

    async def test_login_missing_fields(self, client: AsyncClient):
        res = await client.post(LOGIN_URL, json={"email": "test@example.com"})
        assert res.status_code == 422


# ---------------------------------------------------------------------------
# POST /auth/refresh  +  rotation
# ---------------------------------------------------------------------------

class TestRefresh:

    async def test_refresh_success(self, client: AsyncClient):
        data = await register_user(client)
        res = await client.post(REFRESH_URL, json={
            "refresh_token": data["refresh_token"]
        })
        assert res.status_code == 200
        new_data = res.json()
        assert "access_token" in new_data
        assert "refresh_token" in new_data

    async def test_refresh_token_rotation(self, client: AsyncClient):
        """Old refresh token must be invalid after rotation."""
        data = await register_user(client)
        old_refresh = data["refresh_token"]

        # Use it once — get a new pair
        res = await client.post(REFRESH_URL, json={"refresh_token": old_refresh})
        assert res.status_code == 200

        # Try to use the old token again — must fail
        res2 = await client.post(REFRESH_URL, json={"refresh_token": old_refresh})
        assert res2.status_code == 401
        assert "revoked" in res2.json()["detail"]

    async def test_refresh_invalid_token(self, client: AsyncClient):
        res = await client.post(REFRESH_URL, json={"refresh_token": "not.a.valid.token"})
        assert res.status_code == 401

    async def test_refresh_with_access_token_fails(self, client: AsyncClient):
        """Access tokens must not be accepted on the refresh endpoint."""
        data = await register_user(client)
        res = await client.post(REFRESH_URL, json={
            "refresh_token": data["access_token"]
        })
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------

class TestLogout:

    async def test_logout_success(self, client: AsyncClient):
        data = await register_user(client)
        res = await client.post(LOGOUT_URL, json={
            "refresh_token": data["refresh_token"]
        })
        assert res.status_code == 204

    async def test_logout_revokes_token(self, client: AsyncClient):
        """After logout, the refresh token must no longer work."""
        data = await register_user(client)
        refresh_token = data["refresh_token"]

        await client.post(LOGOUT_URL, json={"refresh_token": refresh_token})

        res = await client.post(REFRESH_URL, json={"refresh_token": refresh_token})
        assert res.status_code == 401

    async def test_logout_invalid_token_still_204(self, client: AsyncClient):
        """Logout with a bogus token should not error — just silently ignore."""
        res = await client.post(LOGOUT_URL, json={"refresh_token": "fake.token.here"})
        assert res.status_code == 204


# ---------------------------------------------------------------------------
# POST /auth/complete-profile
# ---------------------------------------------------------------------------

class TestCompleteProfile:

    async def _register_and_get_headers(self, client: AsyncClient) -> tuple[dict, dict]:
        """Register a user and return (response_data, auth_headers)."""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        return data, headers

    async def test_complete_profile_blocked_for_normal_users(self, client: AsyncClient):
        """Regular email users already have is_profile_complete=True — must get 400."""
        _, headers = await self._register_and_get_headers(client)
        res = await client.post(
            COMPLETE_PROFILE_URL,
            json={"age": 28, "gender": "female"},
            headers=headers,
        )
        assert res.status_code == 400
        assert "already complete" in res.json()["detail"]

    async def test_complete_profile_requires_auth(self, client: AsyncClient):
        res = await client.post(
            COMPLETE_PROFILE_URL,
            json={"age": 28, "gender": "female"},
        )
        assert res.status_code == 401

    async def test_complete_profile_invalid_age(self, client: AsyncClient):
        _, headers = await self._register_and_get_headers(client)
        res = await client.post(
            COMPLETE_PROFILE_URL,
            json={"age": 15, "gender": "male"},
            headers=headers,
        )
        assert res.status_code == 422

    async def test_complete_profile_invalid_gender(self, client: AsyncClient):
        _, headers = await self._register_and_get_headers(client)
        res = await client.post(
            COMPLETE_PROFILE_URL,
            json={"age": 25, "gender": "unknown"},
            headers=headers,
        )
        assert res.status_code == 422


# ---------------------------------------------------------------------------
# POST /auth/change-password
# ---------------------------------------------------------------------------

class TestChangePassword:
    
    async def _register_and_get_headers(self, client: AsyncClient) -> tuple[dict, dict, str]:
        """Register a user and return (response_data, auth_headers, user_id)."""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        return data, headers, data["user"]["id"]
    
    async def test_change_password_success(self, client: AsyncClient):
        """Change password should work with correct old password."""
        data, headers, user_id = await self._register_and_get_headers(client)
        
        res = await client.post(
            CHANGE_PASSWORD_URL,
            json={"old_password": "strongpass123", "new_password": "newpass456"},
            headers=headers,
        )
        assert res.status_code == 204
        
        # Old password should not work anymore
        login_res = await client.post(LOGIN_URL, json={
            "email": VALID_REGISTER_PAYLOAD["email"],
            "password": "strongpass123",
        })
        assert login_res.status_code == 401
        
        # New password should work
        login_res2 = await client.post(LOGIN_URL, json={
            "email": VALID_REGISTER_PAYLOAD["email"],
            "password": "newpass456",
        })
        assert login_res2.status_code == 200
    
    async def test_change_password_revokes_all_tokens(self, client: AsyncClient):
        """After password change, all existing tokens should be invalid."""
        data, headers, user_id = await self._register_and_get_headers(client)
        old_refresh = data["refresh_token"]
        
        # Change password
        res = await client.post(
            CHANGE_PASSWORD_URL,
            json={"old_password": "strongpass123", "new_password": "newpass456"},
            headers=headers,
        )
        assert res.status_code == 204
        
        # Old refresh token should be rejected
        res3 = await client.post(REFRESH_URL, json={"refresh_token": old_refresh})
        assert res3.status_code == 401
        
        # New login should work
        login_res = await client.post(LOGIN_URL, json={
            "email": VALID_REGISTER_PAYLOAD["email"],
            "password": "newpass456",
        })
        assert login_res.status_code == 200
    
    async def test_change_password_wrong_old_password(self, client: AsyncClient):
        """Wrong old password should be rejected."""
        _, headers, _ = await self._register_and_get_headers(client)
        
        res = await client.post(
            CHANGE_PASSWORD_URL,
            json={"old_password": "wrongpassword", "new_password": "newpass456"},
            headers=headers,
        )
        assert res.status_code == 401
        assert "Incorrect old password" in res.json()["detail"]
    
    async def test_change_password_weak_new_password(self, client: AsyncClient):
        """New password must meet requirements."""
        _, headers, _ = await self._register_and_get_headers(client)
        
        res = await client.post(
            CHANGE_PASSWORD_URL,
            json={"old_password": "strongpass123", "new_password": "weak"},
            headers=headers,
        )
        assert res.status_code == 400
        assert "at least 8 characters" in res.json()["detail"]
    
    async def test_change_password_missing_fields(self, client: AsyncClient):
        """Both old and new passwords are required."""
        _, headers, _ = await self._register_and_get_headers(client)
        
        res = await client.post(
            CHANGE_PASSWORD_URL,
            json={"old_password": "strongpass123"},
            headers=headers,
        )
        assert res.status_code == 400
    
    async def test_change_password_requires_auth(self, client: AsyncClient):
        """Cannot change password without authentication."""
        res = await client.post(
            CHANGE_PASSWORD_URL,
            json={"old_password": "strongpass123", "new_password": "newpass456"},
        )
        assert res.status_code == 401
    
    async def test_google_user_cannot_change_password(self, client: AsyncClient):
        """Users who signed up with Google cannot change password."""
        # This test would need a valid Google token
        # Skipping for now
        pass


# ---------------------------------------------------------------------------
# GET /auth/health
# ---------------------------------------------------------------------------

class TestHealthCheck:
    
    async def test_health_check_returns_redis_status(self, client: AsyncClient):
        """Health endpoint should show Redis status."""
        res = await client.get(HEALTH_URL)
        assert res.status_code == 200
        data = res.json()
        assert "status" in data
        assert "redis" in data
        # Should be healthy in test environment
        assert data["redis"] == "connected"


# ---------------------------------------------------------------------------
# Token Versioning Tests
# ---------------------------------------------------------------------------

class TestTokenVersioning:
    
    async def test_token_contains_version(self, client: AsyncClient):
        """Access token should contain version number."""
        data = await register_user(client)
        
        # Decode the access token to check version using jose
        payload = jwt.decode(
            data["access_token"], 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        assert "ver" in payload
        assert payload["ver"] == 1
    
    async def test_login_increments_token_version(self, client: AsyncClient):
        """Login should use current token version."""
        data = await register_user(client)
        
        # First login - version 1
        payload1 = jwt.decode(
            data["access_token"], 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        assert payload1["ver"] == 1
        
        # Login again - still version 1 (password not changed)
        login_res = await client.post(LOGIN_URL, json={
            "email": VALID_REGISTER_PAYLOAD["email"],
            "password": VALID_REGISTER_PAYLOAD["password"],
        })
        assert login_res.status_code == 200
        data2 = login_res.json()
        
        payload2 = jwt.decode(
            data2["access_token"], 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        # Version should still be 1 (password unchanged)
        assert payload2["ver"] == 1
    
    async def test_token_version_increments_after_password_change(self, client: AsyncClient):
        """Token version should increment after password change."""
        data, headers, user_id = await TestChangePassword()._register_and_get_headers(client)
        
        # Check initial version
        payload1 = jwt.decode(
            data["access_token"], 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        assert payload1["ver"] == 1
        
        # Change password
        res = await client.post(
            CHANGE_PASSWORD_URL,
            json={"old_password": "strongpass123", "new_password": "newpass456"},
            headers=headers,
        )
        assert res.status_code == 204
        
        # Login again and check new version
        login_res = await client.post(LOGIN_URL, json={
            "email": VALID_REGISTER_PAYLOAD["email"],
            "password": "newpass456",
        })
        assert login_res.status_code == 200
        data2 = login_res.json()
        
        payload2 = jwt.decode(
            data2["access_token"], 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        # Version should be 2 after password change
        assert payload2["ver"] == 2