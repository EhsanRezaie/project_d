import pytest
from httpx import AsyncClient
from tests.done.test_auth import register_user
from app.core.config import settings

ADMIN_REPORTS_URL = "/api/v1/admin/reports"
ADMIN_KEY = settings.ADMIN_SECRET_KEY


class TestAdminReports:
    """Test admin report management"""

    async def test_admin_list_reports_success(self, client: AsyncClient):
        """Admin should list all reports"""
        # Create a report first
        reporter_data = await register_user(client)
        reporter_headers = {"Authorization": f"Bearer {reporter_data['access_token']}"}
        
        target_payload = {
            "email": "report_target@example.com",
            "password": "strongpass123",
            "name": "Target User",
            "age": 25,
            "gender": "female"
        }
        target_res = await client.post("/api/v1/auth/register", json=target_payload)
        target_data = target_res.json()
        
        await client.post(
            f"/api/v1/reports/{target_data['user']['id']}",
            json={"reason": "Inappropriate behavior"},
            headers=reporter_headers
        )
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(ADMIN_REPORTS_URL, headers=admin_headers)
        assert res.status_code == 200
        body = res.json()
        assert len(body) >= 1

    async def test_admin_list_reports_filter_by_status(self, client: AsyncClient):
        """Admin should filter reports by status"""
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        
        res = await client.get(
            ADMIN_REPORTS_URL,
            params={"status_filter": "pending"},
            headers=admin_headers
        )
        assert res.status_code == 200

    async def test_admin_get_report_detail(self, client: AsyncClient):
        """Admin should view report details"""
        # Create a report
        reporter_data = await register_user(client)
        reporter_headers = {"Authorization": f"Bearer {reporter_data['access_token']}"}
        
        target_payload = {
            "email": "detail_target@example.com",
            "password": "strongpass123",
            "name": "Detail Target",
            "age": 25,
            "gender": "female"
        }
        target_res = await client.post("/api/v1/auth/register", json=target_payload)
        target_data = target_res.json()
        
        report_res = await client.post(
            f"/api/v1/reports/{target_data['user']['id']}",
            json={"reason": "Testing report detail"},
            headers=reporter_headers
        )
        report_id = report_res.json()["id"]
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(f"{ADMIN_REPORTS_URL}/{report_id}", headers=admin_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["id"] == report_id
        assert body["reason"] == "Testing report detail"
        assert "reporter_name" in body
        assert "reported_name" in body

    async def test_admin_review_report(self, client: AsyncClient):
        """Admin should review and take action on report"""
        # Create a report
        reporter_data = await register_user(client)
        reporter_headers = {"Authorization": f"Bearer {reporter_data['access_token']}"}
        
        target_payload = {
            "email": "review_target@example.com",
            "password": "strongpass123",
            "name": "Review Target",
            "age": 25,
            "gender": "female"
        }
        target_res = await client.post("/api/v1/auth/register", json=target_payload)
        target_data = target_res.json()
        
        report_res = await client.post(
            f"/api/v1/reports/{target_data['user']['id']}",
            json={"reason": "Report for review"},
            headers=reporter_headers
        )
        report_id = report_res.json()["id"]
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.patch(
            f"{ADMIN_REPORTS_URL}/{report_id}",
            json={"status": "action_taken", "admin_note": "User warned"},
            headers=admin_headers
        )
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "action_taken"
        assert body["admin_note"] == "User warned"

    async def test_admin_delete_report(self, client: AsyncClient):
        """Admin should delete a report"""
        # Create a report
        reporter_data = await register_user(client)
        reporter_headers = {"Authorization": f"Bearer {reporter_data['access_token']}"}
        
        target_payload = {
            "email": "delete_target@example.com",
            "password": "strongpass123",
            "name": "Delete Target",
            "age": 25,
            "gender": "female"
        }
        target_res = await client.post("/api/v1/auth/register", json=target_payload)
        target_data = target_res.json()
        
        report_res = await client.post(
            f"/api/v1/reports/{target_data['user']['id']}",
            json={"reason": "Report to delete"},
            headers=reporter_headers
        )
        report_id = report_res.json()["id"]
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.delete(f"{ADMIN_REPORTS_URL}/{report_id}", headers=admin_headers)
        assert res.status_code == 204
        
        # Verify deleted
        get_res = await client.get(f"{ADMIN_REPORTS_URL}/{report_id}", headers=admin_headers)
        assert get_res.status_code == 404

    async def test_admin_reports_requires_admin_key(self, client: AsyncClient):
        """Should return 403 without admin key"""
        res = await client.get(ADMIN_REPORTS_URL)
        assert res.status_code == 403