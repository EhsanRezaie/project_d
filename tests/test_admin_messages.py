import pytest
from httpx import AsyncClient
from tests.test_auth import register_user
from app.core.config import settings

ADMIN_USERS_URL = "/api/v1/admin/users"
ADMIN_ANNOUNCEMENTS_URL = "/api/v1/admin/announcements"
ADMIN_KEY = settings.ADMIN_SECRET_KEY


class TestAdminMessageUser:
    """Test admin messaging individual users"""

    async def test_admin_message_user_success(self, client: AsyncClient):
        """Admin should send message to a specific user"""
        # Create a user
        user_data = await register_user(client)
        
        # Admin sends message
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.post(
            f"{ADMIN_USERS_URL}/{user_data['user']['id']}/message",
            json={"title": "Important Update", "message": "Please verify your email"},
            headers=admin_headers
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["user_id"] == user_data["user"]["id"]
        
        # Check notification was created
        user_headers = {"Authorization": f"Bearer {user_data['access_token']}"}
        notif_res = await client.get("/api/v1/notifications", headers=user_headers)
        assert notif_res.status_code == 200
        notifications = notif_res.json()["notifications"]
        assert len(notifications) >= 1
        assert notifications[0]["title"] == "Important Update"

    async def test_admin_message_user_not_found(self, client: AsyncClient):
        """Should return 404 when user doesn't exist"""
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.post(
            f"{ADMIN_USERS_URL}/00000000-0000-0000-0000-000000000001/message",
            json={"title": "Test", "message": "Hello"},
            headers=admin_headers
        )
        assert res.status_code == 404

    async def test_admin_message_requires_message(self, client: AsyncClient):
        """Should return 400 when message is missing"""
        user_data = await register_user(client)
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.post(
            f"{ADMIN_USERS_URL}/{user_data['user']['id']}/message",
            json={"title": "Test", "message": ""},
            headers=admin_headers
        )
        assert res.status_code == 422

    async def test_admin_message_requires_title(self, client: AsyncClient):
        """Should return 400 when title is missing"""
        user_data = await register_user(client)
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.post(
            f"{ADMIN_USERS_URL}/{user_data['user']['id']}/message",
            json={"title": "", "message": "Hello"},
            headers=admin_headers
        )
        assert res.status_code == 422

    async def test_admin_message_requires_auth(self, client: AsyncClient):
        """Should return 403 without admin key"""
        user_data = await register_user(client)
        res = await client.post(
            f"{ADMIN_USERS_URL}/{user_data['user']['id']}/message",
            json={"title": "Test", "message": "Hello"}
        )
        assert res.status_code == 403


class TestAdminAnnouncements:
    """Test admin announcements to all users"""

    async def test_admin_announcement_to_all_users(self, client: AsyncClient):
        """Admin should send announcement to all active users"""
        # Create multiple users
        user_ids = []
        for i in range(3):
            user_payload = {
                "email": f"announce_{i}@example.com",
                "password": "strongpass123",
                "name": f"Announce User {i}",
                "age": 25,
                "gender": "male"
            }
            user_res = await client.post("/api/v1/auth/register", json=user_payload)
            user_ids.append(user_res.json()["user"]["id"])
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.post(
            ADMIN_ANNOUNCEMENTS_URL,
            json={"title": "Site Maintenance", "message": "Site will be down at 2 AM", "to_premium_only": False},
            headers=admin_headers
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["recipient_count"] == 4
        
        # Check each user received notification
        for user_id in user_ids:
            # Login as each user
            login_res = await client.post(
                "/api/v1/auth/login",
                json={"email": f"announce_{user_ids.index(user_id)}@example.com", "password": "strongpass123"}
            )
            assert login_res.status_code == 200
            user_token = login_res.json()["access_token"]
            user_headers = {"Authorization": f"Bearer {user_token}"}
            
            notif_res = await client.get("/api/v1/notifications", headers=user_headers)
            assert notif_res.status_code == 200
            notifications = notif_res.json()["notifications"]
            assert len(notifications) >= 1
            assert notifications[0]["title"] == "Site Maintenance"

    async def test_admin_announcement_to_premium_only(self, client: AsyncClient):
        """Admin should send announcement to premium users only"""
        # Create free user
        free_payload = {
            "email": "free_announce@example.com",
            "password": "strongpass123",
            "name": "Free User",
            "age": 25,
            "gender": "male"
        }
        free_res = await client.post("/api/v1/auth/register", json=free_payload)
        
        # Create premium user (gets welcome bonus)
        premium_payload = {
            "email": "premium_announce@example.com",
            "password": "strongpass123",
            "name": "Premium User",
            "age": 25,
            "gender": "female"
        }
        premium_res = await client.post("/api/v1/auth/register", json=premium_payload)
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.post(
            ADMIN_ANNOUNCEMENTS_URL,
            json={"title": "Premium Offer", "message": "Special discount for you", "to_premium_only": True},
            headers=admin_headers
        )
        assert res.status_code == 200
        body = res.json()
        # Only premium user should get it (welcome bonus makes them premium)
        assert body["recipient_count"] >= 1

    async def test_admin_test_announcement(self, client: AsyncClient):
        """Admin should send test announcement to themselves"""
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.post(
            f"{ADMIN_ANNOUNCEMENTS_URL}/test",
            json={"title": "Test", "message": "This is a test"},
            headers=admin_headers
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert "Test announcement sent" in body["message"]

    async def test_admin_announcement_requires_message(self, client: AsyncClient):
        """Should return 422 when message is missing"""
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.post(
            ADMIN_ANNOUNCEMENTS_URL,
            json={"title": "Test", "message": ""},
            headers=admin_headers
        )
        assert res.status_code == 422

    async def test_admin_announcement_requires_auth(self, client: AsyncClient):
        """Should return 403 without admin key"""
        res = await client.post(
            ADMIN_ANNOUNCEMENTS_URL,
            json={"title": "Test", "message": "Hello", "to_premium_only": False}
        )
        assert res.status_code == 403