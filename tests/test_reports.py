import pytest
from httpx import AsyncClient
from tests.test_auth import register_user

REPORTS_URL = "/api/v1/reports"


class TestReports:
    """Test user reporting system"""

    async def test_report_user_success(self, client: AsyncClient):
        """Should successfully report a user"""
        # Register reporter
        reporter_data = await register_user(client)
        reporter_headers = {"Authorization": f"Bearer {reporter_data['access_token']}"}
        
        # Register target user
        target_payload = {
            "email": "target@example.com",
            "password": "strongpass123",
            "name": "Target User",
            "age": 25,
            "gender": "female"
        }
        target_res = await client.post("/api/v1/auth/register", json=target_payload)
        target_data = target_res.json()
        
        # Report target
        res = await client.post(
            f"{REPORTS_URL}/{target_data['user']['id']}",
            json={"reason": "Inappropriate behavior - sending unwanted messages"},
            headers=reporter_headers
        )
        assert res.status_code == 201
        body = res.json()
        assert body["reported_user_id"] == target_data["user"]["id"]
        assert body["reason"] == "Inappropriate behavior - sending unwanted messages"
        assert body["status"] == "pending"
        assert "created_at" in body

    async def test_report_user_minimal_reason(self, client: AsyncClient):
        """Should accept short but valid reason (min 5 chars)"""
        reporter_data = await register_user(client)
        reporter_headers = {"Authorization": f"Bearer {reporter_data['access_token']}"}
        
        target_payload = {
            "email": "target2@example.com",
            "password": "strongpass123",
            "name": "Target 2",
            "age": 25,
            "gender": "female"
        }
        target_res = await client.post("/api/v1/auth/register", json=target_payload)
        target_data = target_res.json()
        
        res = await client.post(
            f"{REPORTS_URL}/{target_data['user']['id']}",
            json={"reason": "Spammy"},
            headers=reporter_headers
        )
        assert res.status_code == 201

    async def test_report_user_reason_too_short(self, client: AsyncClient):
        """Should reject reason shorter than 5 characters"""
        reporter_data = await register_user(client)
        reporter_headers = {"Authorization": f"Bearer {reporter_data['access_token']}"}
        
        target_payload = {
            "email": "target3@example.com",
            "password": "strongpass123",
            "name": "Target 3",
            "age": 25,
            "gender": "female"
        }
        target_res = await client.post("/api/v1/auth/register", json=target_payload)
        target_data = target_res.json()
        
        res = await client.post(
            f"{REPORTS_URL}/{target_data['user']['id']}",
            json={"reason": "Bad"},
            headers=reporter_headers
        )
        assert res.status_code == 422  # Validation error

    async def test_report_user_reason_too_long(self, client: AsyncClient):
        """Should reject reason longer than 500 characters"""
        reporter_data = await register_user(client)
        reporter_headers = {"Authorization": f"Bearer {reporter_data['access_token']}"}
        
        target_payload = {
            "email": "target4@example.com",
            "password": "strongpass123",
            "name": "Target 4",
            "age": 25,
            "gender": "female"
        }
        target_res = await client.post("/api/v1/auth/register", json=target_payload)
        target_data = target_res.json()
        
        long_reason = "a" * 501
        res = await client.post(
            f"{REPORTS_URL}/{target_data['user']['id']}",
            json={"reason": long_reason},
            headers=reporter_headers
        )
        assert res.status_code == 422

    async def test_cannot_report_self(self, client: AsyncClient):
        """Should not allow reporting yourself"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.post(
            f"{REPORTS_URL}/{data['user']['id']}",
            json={"reason": "Testing self report"},
            headers=headers
        )
        assert res.status_code == 400
        assert "Cannot report yourself" in res.json()["detail"]

    async def test_cannot_report_nonexistent_user(self, client: AsyncClient):
        """Should return 404 when reporting non-existent user"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.post(
            f"{REPORTS_URL}/00000000-0000-0000-0000-000000000001",
            json={"reason": "This user doesn't exist"},
            headers=headers
        )
        assert res.status_code == 404
        assert "User not found" in res.json()["detail"]

    async def test_cannot_report_same_user_twice_in_24h(self, client: AsyncClient):
        """Should prevent reporting the same user twice within 24 hours"""
        reporter_data = await register_user(client)
        reporter_headers = {"Authorization": f"Bearer {reporter_data['access_token']}"}
        
        target_payload = {
            "email": "target5@example.com",
            "password": "strongpass123",
            "name": "Target 5",
            "age": 25,
            "gender": "female"
        }
        target_res = await client.post("/api/v1/auth/register", json=target_payload)
        target_data = target_res.json()
        
        # First report
        res1 = await client.post(
            f"{REPORTS_URL}/{target_data['user']['id']}",
            json={"reason": "First report"},
            headers=reporter_headers
        )
        assert res1.status_code == 201
        
        # Second report within 24h
        res2 = await client.post(
            f"{REPORTS_URL}/{target_data['user']['id']}",
            json={"reason": "Second report"},
            headers=reporter_headers
        )
        assert res2.status_code == 400
        assert "already reported this user recently" in res2.json()["detail"]

    async def test_report_multiple_different_users_allowed(self, client: AsyncClient):
        """Should allow reporting different users"""
        reporter_data = await register_user(client)
        reporter_headers = {"Authorization": f"Bearer {reporter_data['access_token']}"}
        
        # Create and report multiple users
        for i in range(3):
            target_payload = {
                "email": f"target_multi_{i}@example.com",
                "password": "strongpass123",
                "name": f"Target Multi {i}",
                "age": 25,
                "gender": "female"
            }
            target_res = await client.post("/api/v1/auth/register", json=target_payload)
            target_data = target_res.json()
            
            res = await client.post(
                f"{REPORTS_URL}/{target_data['user']['id']}",
                json={"reason": f"Report #{i}"},
                headers=reporter_headers
            )
            assert res.status_code == 201

    async def test_report_requires_auth(self, client: AsyncClient):
        """Should return 401 without authentication"""
        res = await client.post(
            f"{REPORTS_URL}/00000000-0000-0000-0000-000000000001",
            json={"reason": "No auth"}
        )
        assert res.status_code == 401

    async def test_get_my_reports_empty(self, client: AsyncClient):
        """Should return empty list when user has no reports"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.get(f"{REPORTS_URL}/my", headers=headers)
        assert res.status_code == 200
        assert res.json() == []

    async def test_get_my_reports_with_data(self, client: AsyncClient):
        """Should return all reports submitted by user"""
        reporter_data = await register_user(client)
        reporter_headers = {"Authorization": f"Bearer {reporter_data['access_token']}"}
        
        # Create and report multiple users
        reported_ids = []
        for i in range(3):
            target_payload = {
                "email": f"target_my_{i}@example.com",
                "password": "strongpass123",
                "name": f"Target My {i}",
                "age": 25,
                "gender": "female"
            }
            target_res = await client.post("/api/v1/auth/register", json=target_payload)
            target_data = target_res.json()
            reported_ids.append(target_data["user"]["id"])
            
            await client.post(
                f"{REPORTS_URL}/{target_data['user']['id']}",
                json={"reason": f"My report #{i}"},
                headers=reporter_headers
            )
        
        # Get my reports
        res = await client.get(f"{REPORTS_URL}/my", headers=reporter_headers)
        assert res.status_code == 200
        reports = res.json()
        assert len(reports) == 3
        
        # Verify all reported users are in response
        report_user_ids = [r["reported_user_id"] for r in reports]
        for reported_id in reported_ids:
            assert str(reported_id) in report_user_ids

    async def test_get_my_reports_requires_auth(self, client: AsyncClient):
        """Should return 401 without authentication"""
        res = await client.get(f"{REPORTS_URL}/my")
        assert res.status_code == 401

    async def test_report_user_who_deleted_account(self, client: AsyncClient):
        """Should still allow reporting (reported_id can be NULL if user deleted)"""
        reporter_data = await register_user(client)
        reporter_headers = {"Authorization": f"Bearer {reporter_data['access_token']}"}
        
        # Create user then soft delete
        target_payload = {
            "email": "target_delete@example.com",
            "password": "strongpass123",
            "name": "Target Delete",
            "age": 25,
            "gender": "female"
        }
        target_res = await client.post("/api/v1/auth/register", json=target_payload)
        target_data = target_res.json()
        target_headers = {"Authorization": f"Bearer {target_data['access_token']}"}
        
        # Soft delete target
        await client.delete("/api/v1/users/me", headers=target_headers)
        
        # Report deleted user
        res = await client.post(
            f"{REPORTS_URL}/{target_data['user']['id']}",
            json={"reason": "User was inappropriate before deletion"},
            headers=reporter_headers
        )
        assert res.status_code == 201