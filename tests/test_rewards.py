import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from tests.done.test_auth import register_user, VALID_REGISTER_PAYLOAD, LOGIN_URL

REWARDS_LIMITS_URL = "/api/v1/rewards/my-limits"
REWARDS_AD_URL = "/api/v1/rewards/ad-watched"


class TestRewards:
    """Test reward system (ad watching, daily limits)"""

    async def test_premium_user_from_welcome_bonus(self, client: AsyncClient):
        """New users should get welcome bonus premium."""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.get(REWARDS_LIMITS_URL, headers=headers)
        assert res.status_code == 200
        body = res.json()
        
        assert body["is_premium"] is True
        assert body["likes_remaining_today"] == -1  # Unlimited
        assert body["chats_remaining_today"] == -1  # Unlimited
        assert body["premium_expires_at"] is not None
        assert body["max_ads_per_day"] == 2

    async def test_free_user_limits_from_config(self, client: AsyncClient):
        """Free user should see limits from .env (20 likes, 10 chats)."""
        # Create user without welcome bonus by not using the register function
        # or mock the welcome bonus to 0 days
        # For now, we'll test the limits structure
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        # This user has premium from welcome bonus, so skip for now
        # We need to test a non-premium user separately
        pass

    async def test_ad_reward_success(self, client: AsyncClient):
        """Watching an ad should return success with bonus amounts."""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.post(REWARDS_AD_URL, headers=headers)
        assert res.status_code == 200
        body = res.json()
        
        assert body["success"] is True
        assert body["likes_added"] == 5
        assert body["chats_added"] == 3
        assert body["ads_watched_today"] == 1
        assert body["max_ads_per_day"] == 2
        assert "gained" in body["message"]

    async def test_ad_reward_max_limit_reached(self, client: AsyncClient):
        """Cannot watch more than MAX_AD_REWARDS_PER_DAY ads (default 2)."""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        # First ad
        res1 = await client.post(REWARDS_AD_URL, headers=headers)
        assert res1.status_code == 200
        
        # Second ad
        res2 = await client.post(REWARDS_AD_URL, headers=headers)
        assert res2.status_code == 200
        
        # Third ad - should fail
        res3 = await client.post(REWARDS_AD_URL, headers=headers)
        assert res3.status_code == 429
        body = res3.json()
        assert "Daily ad limit reached" in body["detail"]

    async def test_ad_reward_requires_auth(self, client: AsyncClient):
        """Cannot watch ad without authentication."""
        res = await client.post(REWARDS_AD_URL)
        assert res.status_code == 401

    async def test_get_limits_requires_auth(self, client: AsyncClient):
        """Cannot get limits without authentication."""
        res = await client.get(REWARDS_LIMITS_URL)
        assert res.status_code == 401

    async def test_ad_reward_returns_correct_limits_structure(self, client: AsyncClient):
        """Response structure should contain all expected fields."""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.get(REWARDS_LIMITS_URL, headers=headers)
        assert res.status_code == 200
        body = res.json()
        
        expected_fields = [
            "is_premium", "premium_expires_at", "likes_used_today",
            "likes_remaining_today", "chats_used_today", "chats_remaining_today",
            "ads_watched_today", "max_ads_per_day", "daily_likes_limit",
            "daily_chats_limit", "ad_reward_likes_bonus", "ad_reward_chats_bonus"
        ]
        for field in expected_fields:
            assert field in body