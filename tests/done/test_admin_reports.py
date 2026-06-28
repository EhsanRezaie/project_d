import pytest
from httpx import AsyncClient
from app.core.config import settings

REGISTER_INIT_URL = "/api/v1/auth/register/init"
REGISTER_VERIFY_URL = "/api/v1/auth/register/verify"
REGISTER_COMPLETE_URL = "/api/v1/auth/register/complete"
ADMIN_REPORTS_URL = "/api/v1/admin/reports"
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


class TestAdminReports:
    """Test admin report management"""

    async def test_admin_list_reports_success(self, client: AsyncClient, mock_verification_code):
        """Admin should list all reports"""
        # Create a report first
        reporter_data = await register_user(client, "report_reporter@example.com", mock_verification_code)
        reporter_headers = {"Authorization": f"Bearer {reporter_data['access_token']}"}

        target_data = await register_user(client, "report_target@example.com", mock_verification_code)

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

    async def test_admin_get_report_detail(self, client: AsyncClient, mock_verification_code):
        """Admin should view report details"""
        # Create a report
        reporter_data = await register_user(client, "detail_reporter@example.com", mock_verification_code)
        reporter_headers = {"Authorization": f"Bearer {reporter_data['access_token']}"}

        target_data = await register_user(client, "detail_target@example.com", mock_verification_code)

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

    async def test_admin_review_report(self, client: AsyncClient, mock_verification_code):
        """Admin should review and take action on report"""
        # Create a report
        reporter_data = await register_user(client, "review_reporter@example.com", mock_verification_code)
        reporter_headers = {"Authorization": f"Bearer {reporter_data['access_token']}"}

        target_data = await register_user(client, "review_target@example.com", mock_verification_code)

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

    async def test_admin_delete_report(self, client: AsyncClient, mock_verification_code):
        """Admin should delete a report"""
        # Create a report
        reporter_data = await register_user(client, "delete_reporter@example.com", mock_verification_code)
        reporter_headers = {"Authorization": f"Bearer {reporter_data['access_token']}"}

        target_data = await register_user(client, "delete_target@example.com", mock_verification_code)

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
