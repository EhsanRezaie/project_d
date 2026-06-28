import pytest
from httpx import AsyncClient
from app.core.config import settings

REGISTER_INIT_URL = "/api/v1/auth/register/init"
REGISTER_VERIFY_URL = "/api/v1/auth/register/verify"
REGISTER_COMPLETE_URL = "/api/v1/auth/register/complete"
ADMIN_TICKETS_URL = "/api/v1/admin/tickets"
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


class TestAdminTickets:
    """Test admin ticket management"""

    async def test_admin_list_tickets_success(self, client: AsyncClient, mock_verification_code):
        """Admin should list all tickets"""
        # Create a regular user with a ticket
        user_data = await register_user(client, "ticket@example.com", mock_verification_code)
        user_headers = {"Authorization": f"Bearer {user_data['access_token']}"}

        await client.post(
            "/api/v1/tickets",
            json={"subject": "Test Ticket", "message": "This is a test ticket"},
            headers=user_headers
        )

        # Admin access
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(ADMIN_TICKETS_URL, headers=admin_headers)
        assert res.status_code == 200
        body = res.json()
        assert "tickets" in body
        assert body["total"] >= 1

    async def test_admin_list_tickets_filter_by_status(self, client: AsyncClient):
        """Admin should filter tickets by status"""
        admin_headers = {"X-Admin-Key": ADMIN_KEY}

        res = await client.get(
            ADMIN_TICKETS_URL,
            params={"status_filter": "open"},
            headers=admin_headers
        )
        assert res.status_code == 200

    async def test_admin_get_ticket_detail(self, client: AsyncClient, mock_verification_code):
        """Admin should view ticket details"""
        # Create a ticket
        user_data = await register_user(client, "ticketdetail@example.com", mock_verification_code)
        user_headers = {"Authorization": f"Bearer {user_data['access_token']}"}

        create_res = await client.post(
            "/api/v1/tickets",
            json={"subject": "Admin View Test", "message": "Please help me"},
            headers=user_headers
        )
        ticket_id = create_res.json()["id"]

        # Admin views ticket
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(f"{ADMIN_TICKETS_URL}/{ticket_id}", headers=admin_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["id"] == ticket_id
        assert body["subject"] == "Admin View Test"
        assert "user_name" in body
        assert "user_email" in body

    async def test_admin_respond_to_ticket(self, client: AsyncClient, mock_verification_code):
        """Admin should respond to ticket and close it"""
        # Create a ticket
        user_data = await register_user(client, "ticketrespond@example.com", mock_verification_code)
        user_headers = {"Authorization": f"Bearer {user_data['access_token']}"}

        create_res = await client.post(
            "/api/v1/tickets",
            json={"subject": "Response Test", "message": "I need help"},
            headers=user_headers
        )
        ticket_id = create_res.json()["id"]

        # Admin responds
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.patch(
            f"{ADMIN_TICKETS_URL}/{ticket_id}",
            json={"admin_response": "We have reviewed your ticket. Please contact support.", "status": "closed"},
            headers=admin_headers
        )
        assert res.status_code == 200
        body = res.json()
        assert body["admin_response"] == "We have reviewed your ticket. Please contact support."
        assert body["status"] == "closed"

    async def test_admin_update_ticket_status_only(self, client: AsyncClient, mock_verification_code):
        """Admin should update ticket status without response"""
        # Create a ticket
        user_data = await register_user(client, "ticketstatus@example.com", mock_verification_code)
        user_headers = {"Authorization": f"Bearer {user_data['access_token']}"}

        create_res = await client.post(
            "/api/v1/tickets",
            json={"subject": "Status Test", "message": "Test message"},
            headers=user_headers
        )
        ticket_id = create_res.json()["id"]

        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.patch(
            f"{ADMIN_TICKETS_URL}/{ticket_id}",
            json={"status": "in_progress"},
            headers=admin_headers
        )
        assert res.status_code == 200
        assert res.json()["status"] == "in_progress"

    async def test_admin_delete_ticket(self, client: AsyncClient, mock_verification_code):
        """Admin should delete a ticket"""
        # Create a ticket
        user_data = await register_user(client, "ticketdelete@example.com", mock_verification_code)
        user_headers = {"Authorization": f"Bearer {user_data['access_token']}"}

        create_res = await client.post(
            "/api/v1/tickets",
            json={"subject": "Delete Test", "message": "This ticket will be deleted"},
            headers=user_headers
        )
        ticket_id = create_res.json()["id"]

        # Admin deletes ticket
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.delete(f"{ADMIN_TICKETS_URL}/{ticket_id}", headers=admin_headers)
        assert res.status_code == 204

        # Verify deleted
        get_res = await client.get(f"{ADMIN_TICKETS_URL}/{ticket_id}", headers=admin_headers)
        assert get_res.status_code == 404

    async def test_admin_tickets_requires_admin_key(self, client: AsyncClient):
        """Should return 403 without admin key"""
        res = await client.get(ADMIN_TICKETS_URL)
        assert res.status_code == 403

    async def test_admin_tickets_wrong_admin_key(self, client: AsyncClient):
        """Should return 403 with wrong admin key"""
        headers = {"X-Admin-Key": "wrong-key"}
        res = await client.get(ADMIN_TICKETS_URL, headers=headers)
        assert res.status_code == 403

    async def test_admin_get_nonexistent_ticket(self, client: AsyncClient):
        """Should return 404 for non-existent ticket"""
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(
            f"{ADMIN_TICKETS_URL}/00000000-0000-0000-0000-000000000001",
            headers=admin_headers
        )
        assert res.status_code == 404
