import pytest
from httpx import AsyncClient
from tests.test_auth import register_user
from app.core.config import settings

ADMIN_TICKETS_URL = "/api/v1/admin/tickets"
ADMIN_KEY = settings.ADMIN_SECRET_KEY  # From your .env


class TestAdminTickets:
    """Test admin ticket management"""

    async def test_admin_list_tickets_success(self, client: AsyncClient):
        """Admin should list all tickets"""
        # Create a regular user with a ticket
        user_data = await register_user(client)
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

    async def test_admin_get_ticket_detail(self, client: AsyncClient):
        """Admin should view ticket details"""
        # Create a ticket
        user_data = await register_user(client)
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

    async def test_admin_respond_to_ticket(self, client: AsyncClient):
        """Admin should respond to ticket and close it"""
        # Create a ticket
        user_data = await register_user(client)
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

    async def test_admin_update_ticket_status_only(self, client: AsyncClient):
        """Admin should update ticket status without response"""
        # Create a ticket
        user_data = await register_user(client)
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

    async def test_admin_delete_ticket(self, client: AsyncClient):
        """Admin should delete a ticket"""
        # Create a ticket
        user_data = await register_user(client)
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