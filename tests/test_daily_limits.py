import pytest
from httpx import AsyncClient
from tests.done.test_auth import register_user, VALID_REGISTER_PAYLOAD

SWIPE_URL = "/api/v1/swipes"
REWARDS_LIMITS_URL = "/api/v1/rewards/my-limits"


class TestDailyLimits:
    """Test daily limits enforcement"""

    async def test_premium_user_unlimited_likes(self, client: AsyncClient):
        """Premium user should have unlimited likes (-1)."""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.get(REWARDS_LIMITS_URL, headers=headers)
        assert res.status_code == 200
        body = res.json()
        
        # Welcome bonus makes user premium
        assert body["likes_remaining_today"] == -1
        assert body["chats_remaining_today"] == -1

    async def test_cannot_swipe_on_self(self, client: AsyncClient):
        """Swiping on yourself should return 400."""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.post(
            SWIPE_URL,
            json={"user_id": data["user"]["id"], "direction": "like"},
            headers=headers
        )
        assert res.status_code == 400
        assert "Cannot swipe on yourself" in res.json()["detail"]

    async def test_cannot_swipe_twice_on_same_user(self, client: AsyncClient):
        """Cannot swipe twice on the same user."""
        # Register two users
        user1_data = await register_user(client)
        user1_headers = {"Authorization": f"Bearer {user1_data['access_token']}"}
        
        user2_payload = {
            "email": "user2@example.com",
            "password": "strongpass123",
            "name": "User Two",
            "age": 25,
            "gender": "female"
        }
        user2_res = await client.post("/api/v1/auth/register", json=user2_payload)
        user2_data = user2_res.json()
        
        # First swipe
        res1 = await client.post(
            SWIPE_URL,
            json={"user_id": user2_data["user"]["id"], "direction": "like"},
            headers=user1_headers
        )
        assert res1.status_code == 200
        
        # Second swipe - should fail
        res2 = await client.post(
            SWIPE_URL,
            json={"user_id": user2_data["user"]["id"], "direction": "like"},
            headers=user1_headers
        )
        assert res2.status_code == 400
        assert "Already swiped" in res2.json()["detail"]

    async def test_swipe_stats_returns_correct_structure(self, client: AsyncClient):
        """Swipe stats endpoint should return correct structure."""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.get("/api/v1/swipes/stats", headers=headers)
        assert res.status_code == 200
        body = res.json()
        
        expected_fields = [
            "daily_likes_remaining", "is_unlimited",
            "total_likes_sent", "total_passes_sent", "total_matches",
            "ads_watched_today", "max_ads_per_day"
        ]
        for field in expected_fields:
            assert field in body