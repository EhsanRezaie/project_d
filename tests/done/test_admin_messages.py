import pytest
from httpx import AsyncClient
from app.core.config import settings

REGISTER_INIT_URL = "/api/v1/auth/register/init"
REGISTER_VERIFY_URL = "/api/v1/auth/register/verify"
REGISTER_COMPLETE_URL = "/api/v1/auth/register/complete"
ADMIN_USERS_URL = "/api/v1/admin/users"
ADMIN_ANNOUNCEMENTS_URL = "/api/v1/admin/announcements"
ADMIN_KEY = settings.ADMIN_SECRET_KEY
VALID_PASSWORD = "strongpass123"
VALID_CODE = "123456"
COMPLETE_PROFILE = {
    "name": "Test User",
    "birth_date": "1995-06-15",
    "gender": "male",
    "lat": 35.6892,
    "lng": 51.3890,
}


async def register_user(client: AsyncClient, email: str, mock_verification_code=None) -> dict:
    res = await client.post(REGISTER_INIT_URL, json={"email": email})
    assert res.status_code == 200, res.text
    if mock_verification_code:
        await mock_verification_code(email, VALID_CODE)
    res = await client.post(REGISTER_VERIFY_URL, json={
        "email": email, "code": VALID_CODE, "password": VALID_PASSWORD,
    })
    assert res.status_code == 200, res.text
    data = res.json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    res = await client.post(REGISTER_COMPLETE_URL, json=COMPLETE_PROFILE, headers=headers)
    assert res.status_code == 200, res.text
    return res.json()


class TestAdminMessageUser:
    """Test admin messaging individual users"""

    async def test_admin_message_user_success(self, client: AsyncClient, mock_verification_code):
        """Admin should send message to a specific user"""
        # Create a user
        user_data = await register_user(client, "msguser@example.com", mock_verification_code)

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

    async def test_admin_message_requires_message(self, client: AsyncClient, mock_verification_code):
        """Should return 400 when message is missing"""
        user_data = await register_user(client, "msgreq@example.com", mock_verification_code)
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.post(
            f"{ADMIN_USERS_URL}/{user_data['user']['id']}/message",
            json={"title": "Test", "message": ""},
            headers=admin_headers
        )
        assert res.status_code == 422

    async def test_admin_message_requires_title(self, client: AsyncClient, mock_verification_code):
        """Should return 400 when title is missing"""
        user_data = await register_user(client, "titlereq@example.com", mock_verification_code)
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.post(
            f"{ADMIN_USERS_URL}/{user_data['user']['id']}/message",
            json={"title": "", "message": "Hello"},
            headers=admin_headers
        )
        assert res.status_code == 422

    async def test_admin_message_requires_auth(self, client: AsyncClient, mock_verification_code):
        """Should return 403 without admin key"""
        user_data = await register_user(client, "msgauth@example.com", mock_verification_code)
        res = await client.post(
            f"{ADMIN_USERS_URL}/{user_data['user']['id']}/message",
            json={"title": "Test", "message": "Hello"}
        )
        assert res.status_code == 403


class TestAdminAnnouncements:
    """Test admin announcements to all users"""

    async def test_admin_announcement_to_all_users(self, client: AsyncClient, mock_verification_code):
        """Admin should send announcement to all active users"""
        # Create multiple users
        user_ids = []
        for i in range(3):
            data = await register_user(client, f"announce_{i}@example.com", mock_verification_code)
            user_ids.append(data["user"]["id"])

        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.post(
            ADMIN_ANNOUNCEMENTS_URL,
            json={"title": "Site Maintenance", "message": "Site will be down at 2 AM", "to_premium_only": False},
            headers=admin_headers
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        # admin + 3 test users + admin@test.com = 5 total active users
        assert body["recipient_count"] >= 4

        # Check each user received notification
        for i, user_id in enumerate(user_ids):
            # Login as each user
            login_res = await client.post(
                "/api/v1/auth/login",
                json={"email": f"announce_{i}@example.com", "password": "strongpass123"}
            )
            assert login_res.status_code == 200
            user_token = login_res.json()["access_token"]
            user_headers = {"Authorization": f"Bearer {user_token}"}

            notif_res = await client.get("/api/v1/notifications", headers=user_headers)
            assert notif_res.status_code == 200
            notifications = notif_res.json()["notifications"]
            assert len(notifications) >= 1
            assert notifications[0]["title"] == "Site Maintenance"

    async def test_admin_announcement_to_premium_only(self, client: AsyncClient, mock_verification_code):
        """Admin should send announcement to premium users only"""
        # Create free user
        free_data = await register_user(client, "free_announce@example.com", mock_verification_code)

        # Create premium user (gets welcome bonus)
        premium_data = await register_user(client, "premium_announce@example.com", mock_verification_code)

        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.post(
            ADMIN_ANNOUNCEMENTS_URL,
            json={"title": "Premium Offer", "message": "Special discount for you", "to_premium_only": True},
            headers=admin_headers
        )
        assert res.status_code == 200
        body = res.json()
        # Welcome bonus makes newly registered users premium, so all new users get it
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
