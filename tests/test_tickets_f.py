import pytest
from httpx import AsyncClient
from tests.done.test_auth import register_user

TICKETS_URL = "/api/v1/tickets"


class TestUserTickets:
    """Test user ticket submission and viewing"""

    async def test_create_ticket_success(self, client: AsyncClient):
        """User should be able to create a support ticket"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.post(
            TICKETS_URL,
            json={
                "subject": "Help with account",
                "message": "I need help with my account settings. Please assist."
            },
            headers=headers
        )
        assert res.status_code == 201
        body = res.json()
        assert body["subject"] == "Help with account"
        assert body["message"] == "I need help with my account settings. Please assist."
        assert body["status"] == "open"
        assert "id" in body

    async def test_create_ticket_subject_too_short(self, client: AsyncClient):
        """Should reject subject shorter than 3 characters"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.post(
            TICKETS_URL,
            json={"subject": "Hi", "message": "This is a test message"},
            headers=headers
        )
        assert res.status_code == 422

    async def test_create_ticket_subject_too_long(self, client: AsyncClient):
        """Should reject subject longer than 200 characters"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.post(
            TICKETS_URL,
            json={"subject": "a" * 201, "message": "Test message"},
            headers=headers
        )
        assert res.status_code == 422

    async def test_create_ticket_message_too_short(self, client: AsyncClient):
        """Should reject message shorter than 10 characters"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.post(
            TICKETS_URL,
            json={"subject": "Help", "message": "Too short"},
            headers=headers
        )
        assert res.status_code == 422

    async def test_create_ticket_message_too_long(self, client: AsyncClient):
        """Should reject message longer than 2000 characters"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.post(
            TICKETS_URL,
            json={"subject": "Help", "message": "a" * 2001},
            headers=headers
        )
        assert res.status_code == 422

    async def test_create_ticket_requires_auth(self, client: AsyncClient):
        """Should return 401 without authentication"""
        res = await client.post(
            TICKETS_URL,
            json={"subject": "Help", "message": "Need assistance"}
        )
        assert res.status_code == 401

    async def test_get_my_tickets_empty(self, client: AsyncClient):
        """Should return empty list when user has no tickets"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.get(TICKETS_URL, headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert body["tickets"] == []
        assert body["total"] == 0

    async def test_get_my_tickets_with_data(self, client: AsyncClient):
        """Should return user's tickets"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        # Create multiple tickets
        for i in range(3):
            await client.post(
                TICKETS_URL,
                json={"subject": f"Ticket {i}", "message": f"Message {i}" * 10},
                headers=headers
            )
        
        res = await client.get(TICKETS_URL, headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert len(body["tickets"]) == 3
        assert body["total"] == 3

    async def test_get_my_tickets_pagination(self, client: AsyncClient):
        """Should paginate tickets correctly"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        for i in range(5):
            await client.post(
                TICKETS_URL,
                json={"subject": f"Ticket {i}", "message": f"Message {i}" * 10},
                headers=headers
            )
        
        res = await client.get(TICKETS_URL, params={"limit": 2}, headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert len(body["tickets"]) == 2
        assert body["total"] == 5
        assert body["next_offset"] == 2

    async def test_get_ticket_detail_success(self, client: AsyncClient):
        """Should return ticket details for user's own ticket"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        create_res = await client.post(
            TICKETS_URL,
            json={"subject": "My Ticket", "message": "This is my ticket message"},
            headers=headers
        )
        ticket_id = create_res.json()["id"]
        
        res = await client.get(f"{TICKETS_URL}/{ticket_id}", headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert body["id"] == ticket_id
        assert body["subject"] == "My Ticket"
        assert body["message"] == "This is my ticket message"

    async def test_get_ticket_detail_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent ticket"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.get(
            f"{TICKETS_URL}/00000000-0000-0000-0000-000000000001",
            headers=headers
        )
        assert res.status_code == 404

    async def test_get_ticket_detail_other_user(self, client: AsyncClient):
        """Should not allow viewing other user's ticket"""
        # Create user A with ticket
        userA_data = await register_user(client)
        userA_headers = {"Authorization": f"Bearer {userA_data['access_token']}"}
        
        create_res = await client.post(
            TICKETS_URL,
            json={"subject": "User A Ticket", "message": "This is user A's ticket"},
            headers=userA_headers
        )
        ticket_id = create_res.json()["id"]
        
        # Create user B trying to view user A's ticket
        userB_payload = {
            "email": "userb@example.com",
            "password": "strongpass123",
            "name": "User B",
            "age": 25,
            "gender": "female"
        }
        userB_res = await client.post("/api/v1/auth/register", json=userB_payload)
        userB_data = userB_res.json()
        userB_headers = {"Authorization": f"Bearer {userB_data['access_token']}"}
        
        res = await client.get(f"{TICKETS_URL}/{ticket_id}", headers=userB_headers)
        assert res.status_code == 404

    async def test_get_ticket_detail_requires_auth(self, client: AsyncClient):
        """Should return 401 without authentication"""
        res = await client.get(f"{TICKETS_URL}/00000000-0000-0000-0000-000000000001")
        assert res.status_code == 401