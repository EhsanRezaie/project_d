import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"
COMPLETE_PROFILE_URL = "/api/v1/auth/complete-profile"

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