import pytest
from httpx import AsyncClient
from tests.done.test_auth import register_user, VALID_REGISTER_PAYLOAD

REFERRAL_CODE_URL = "/api/v1/referrals/my-code"
REFERRAL_CLAIM_URL = "/api/v1/referrals/claim"
REFERRAL_STATS_URL = "/api/v1/referrals/stats"


class TestReferrals:
    """Test referral system"""

    async def test_get_referral_code(self, client: AsyncClient):
        """User should get a unique referral code."""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.get(REFERRAL_CODE_URL, headers=headers)
        assert res.status_code == 200
        body = res.json()
        
        assert "referral_code" in body
        assert len(body["referral_code"]) == 8
        assert "share_text" in body
        assert "Join me on DatingApp" in body["share_text"]

    async def test_referral_code_persists(self, client: AsyncClient):
        """Referral code should be the same on subsequent requests."""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res1 = await client.get(REFERRAL_CODE_URL, headers=headers)
        code1 = res1.json()["referral_code"]
        
        res2 = await client.get(REFERRAL_CODE_URL, headers=headers)
        code2 = res2.json()["referral_code"]
        
        assert code1 == code2

    async def test_claim_referral_success(self, client: AsyncClient):
        """Claiming a valid referral code should grant premium to both."""
        # Register first user (inviter)
        inviter_data = await register_user(client)
        inviter_headers = {"Authorization": f"Bearer {inviter_data['access_token']}"}
        
        # Get inviter's referral code
        code_res = await client.get(REFERRAL_CODE_URL, headers=inviter_headers)
        referral_code = code_res.json()["referral_code"]
        
        # Register second user (invited) WITH referral code
        invited_payload = {
            "email": "invited@example.com",
            "password": "strongpass123",
            "name": "Invited User",
            "age": 25,
            "gender": "female",
            "referral_code": referral_code
        }
        invited_res = await client.post("/api/v1/auth/register", json=invited_payload)
        assert invited_res.status_code == 201
        
        # Check inviter stats
        inviter_stats = await client.get(REFERRAL_STATS_URL, headers=inviter_headers)
        assert inviter_stats.status_code == 200
        stats = inviter_stats.json()
        assert stats["successful_referrals"] == 1
        assert stats["total_premium_days_earned"] == 3

    async def test_claim_referral_requires_code(self, client: AsyncClient):
        """Claim endpoint requires referral_code in body."""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.post(REFERRAL_CLAIM_URL, json={}, headers=headers)
        assert res.status_code == 400
        assert "Referral code required" in res.json()["detail"]

    async def test_claim_invalid_referral_code(self, client: AsyncClient):
        """Claiming invalid code should return 404."""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.post(
            REFERRAL_CLAIM_URL,
            json={"referral_code": "INVALID123"},
            headers=headers
        )
        assert res.status_code == 404
        assert "Invalid referral code" in res.json()["detail"]

    async def test_cannot_use_own_referral_code(self, client: AsyncClient):
        """User cannot claim their own referral code."""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        # Get own code
        code_res = await client.get(REFERRAL_CODE_URL, headers=headers)
        own_code = code_res.json()["referral_code"]
        
        # Try to claim own code
        res = await client.post(
            REFERRAL_CLAIM_URL,
            json={"referral_code": own_code},
            headers=headers
        )
        assert res.status_code == 400
        assert "Cannot use your own referral code" in res.json()["detail"]

    async def test_cannot_claim_referral_twice(self, client: AsyncClient):
        """User can only claim a referral once."""
        # Register inviter
        inviter_data = await register_user(client)
        inviter_headers = {"Authorization": f"Bearer {inviter_data['access_token']}"}
        code_res = await client.get(REFERRAL_CODE_URL, headers=inviter_headers)
        referral_code = code_res.json()["referral_code"]
        
        # Register invited user with code
        invited_payload = {
            "email": "invited2@example.com",
            "password": "strongpass123",
            "name": "Invited User 2",
            "age": 25,
            "gender": "female",
            "referral_code": referral_code
        }
        invited_res = await client.post("/api/v1/auth/register", json=invited_payload)
        assert invited_res.status_code == 201
        invited_data = invited_res.json()
        invited_headers = {"Authorization": f"Bearer {invited_data['access_token']}"}
        
        # Try to claim again (should fail)
        res = await client.post(
            REFERRAL_CLAIM_URL,
            json={"referral_code": "ANOTHER123"},
            headers=invited_headers
        )
        assert res.status_code == 400
        assert "Referral already claimed" in res.json()["detail"]

    async def test_referral_stats_structure(self, client: AsyncClient):
        """Referral stats should return correct structure."""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.get(REFERRAL_STATS_URL, headers=headers)
        assert res.status_code == 200
        body = res.json()
        
        expected_fields = [
            "referral_code", "successful_referrals", "total_premium_days_earned",
            "inviter_reward_days", "invited_reward_days", "is_premium", "premium_until"
        ]
        for field in expected_fields:
            assert field in body

    async def test_referral_requires_auth(self, client: AsyncClient):
        """All referral endpoints require authentication."""
        # my-code
        res1 = await client.get(REFERRAL_CODE_URL)
        assert res1.status_code == 401
        
        # claim
        res2 = await client.post(REFERRAL_CLAIM_URL, json={"referral_code": "TEST123"})
        assert res2.status_code == 401
        
        # stats
        res3 = await client.get(REFERRAL_STATS_URL)
        assert res3.status_code == 401