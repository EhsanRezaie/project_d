import pytest
from httpx import AsyncClient
from tests.done.test_auth import register_user
from app.core.config import settings

ADMIN_USERS_URL = "/api/v1/admin/users"
ADMIN_KEY = settings.ADMIN_SECRET_KEY


class TestAdminUsers:
    """Test admin user management"""

    async def test_admin_list_users_success(self, client: AsyncClient):
        """Admin should list all users"""
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(ADMIN_USERS_URL, headers=admin_headers)
        assert res.status_code == 200
        body = res.json()
        assert "users" in body
        assert "total" in body

    async def test_admin_list_users_search_by_name(self, client: AsyncClient):
        """Admin should search users by name"""
        # Create a user with unique name
        user_payload = {
            "email": "search_test@example.com",
            "password": "strongpass123",
            "name": "SearchableUserName",
            "age": 25,
            "gender": "male"
        }
        await client.post("/api/v1/auth/register", json=user_payload)
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(
            ADMIN_USERS_URL,
            params={"search": "SearchableUserName"},
            headers=admin_headers
        )
        assert res.status_code == 200
        body = res.json()
        assert len(body["users"]) >= 1
        assert body["users"][0]["name"] == "SearchableUserName"

    async def test_admin_list_users_search_by_email(self, client: AsyncClient):
        """Admin should search users by email"""
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(
            ADMIN_USERS_URL,
            params={"search": "search_test@example.com"},
            headers=admin_headers
        )
        assert res.status_code == 200

    async def test_admin_list_users_filter_active(self, client: AsyncClient):
        """Admin should filter active users"""
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(
            ADMIN_USERS_URL,
            params={"is_active": True},
            headers=admin_headers
        )
        assert res.status_code == 200

    async def test_admin_list_users_filter_inactive(self, client: AsyncClient):
        """Admin should filter inactive users"""
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(
            ADMIN_USERS_URL,
            params={"is_active": False},
            headers=admin_headers
        )
        assert res.status_code == 200

    async def test_admin_list_users_filter_premium(self, client: AsyncClient):
        """Admin should filter premium users"""
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(
            ADMIN_USERS_URL,
            params={"is_premium": True},
            headers=admin_headers
        )
        assert res.status_code == 200

    async def test_admin_list_users_pagination(self, client: AsyncClient):
        """Admin should paginate users"""
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(
            ADMIN_USERS_URL,
            params={"limit": 5, "offset": 0},
            headers=admin_headers
        )
        assert res.status_code == 200
        body = res.json()
        assert len(body["users"]) <= 5

    async def test_admin_get_user_detail(self, client: AsyncClient):
        """Admin should view user details with stats"""
        # Create a user
        user_data = await register_user(client)
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(
            f"{ADMIN_USERS_URL}/{user_data['user']['id']}",
            headers=admin_headers
        )
        assert res.status_code == 200
        body = res.json()
        assert body["id"] == str(user_data['user']['id'])
        assert body["email"] == user_data['user']['email']
        assert "total_likes_sent" in body
        assert "total_matches" in body
        assert "total_messages" in body

    async def test_admin_get_nonexistent_user(self, client: AsyncClient):
        """Should return 404 for non-existent user"""
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(
            f"{ADMIN_USERS_URL}/00000000-0000-0000-0000-000000000001",
            headers=admin_headers
        )
        assert res.status_code == 404

    async def test_admin_deactivate_user(self, client: AsyncClient):
        """Admin should deactivate a user"""
        # Create a user
        user_data = await register_user(client)
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.patch(
            f"{ADMIN_USERS_URL}/{user_data['user']['id']}",
            json={"is_active": False},
            headers=admin_headers
        )
        assert res.status_code == 200
        body = res.json()
        assert body["is_active"] is False
        
        # User should not be able to login
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": user_data['user']['email'], "password": "strongpass123"}
        )
        assert login_res.status_code == 401

    async def test_admin_activate_user(self, client: AsyncClient):
        """Admin should activate a deactivated user"""
        # Create a user
        user_data = await register_user(client)
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        
        # Deactivate
        await client.patch(
            f"{ADMIN_USERS_URL}/{user_data['user']['id']}",
            json={"is_active": False},
            headers=admin_headers
        )
        
        # Activate
        res = await client.patch(
            f"{ADMIN_USERS_URL}/{user_data['user']['id']}",
            json={"is_active": True},
            headers=admin_headers
        )
        assert res.status_code == 200
        assert res.json()["is_active"] is True

    async def test_admin_grant_premium(self, client: AsyncClient):
        """Admin should grant premium days to user"""
        # Create a user
        user_data = await register_user(client)
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.post(
            f"{ADMIN_USERS_URL}/{user_data['user']['id']}/premium",
            json={"days": 30},
            headers=admin_headers
        )
        assert res.status_code == 200
        body = res.json()
        assert body["is_premium"] is True
        assert body["premium_until"] is not None

    async def test_admin_delete_user(self, client: AsyncClient):
        """Admin should hard delete a user"""
        # Create a user
        user_payload = {
            "email": "delete_me@example.com",
            "password": "strongpass123",
            "name": "Delete Me",
            "age": 25,
            "gender": "male"
        }
        user_res = await client.post("/api/v1/auth/register", json=user_payload)
        user_id = user_res.json()["user"]["id"]
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.delete(f"{ADMIN_USERS_URL}/{user_id}", headers=admin_headers)
        assert res.status_code == 204
        
        # User should not exist
        get_res = await client.get(f"{ADMIN_USERS_URL}/{user_id}", headers=admin_headers)
        assert get_res.status_code == 404

    async def test_admin_get_user_activity(self, client: AsyncClient):
        """Admin should get user activity stats"""
        # Create a user and do some activity
        user_data = await register_user(client)
        user_headers = {"Authorization": f"Bearer {user_data['access_token']}"}
        
        # Create another user to swipe
        target_payload = {
            "email": "activity_target@example.com",
            "password": "strongpass123",
            "name": "Activity Target",
            "age": 25,
            "gender": "female"
        }
        target_res = await client.post("/api/v1/auth/register", json=target_payload)
        target_data = target_res.json()
        
        # Perform a swipe
        await client.post(
            "/api/v1/swipes",
            json={"user_id": target_data["user"]["id"], "direction": "like"},
            headers=user_headers
        )
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(
            f"{ADMIN_USERS_URL}/{user_data['user']['id']}/activity",
            params={"days": 7},
            headers=admin_headers
        )
        assert res.status_code == 200
        body = res.json()
        assert len(body) >= 1
        assert "date" in body[0]
        assert "swipes" in body[0]

    async def test_admin_users_requires_admin_key(self, client: AsyncClient):
        """Should return 403 without admin key"""
        res = await client.get(ADMIN_USERS_URL)
        assert res.status_code == 403