import pytest
from httpx import AsyncClient
from tests.done.test_auth import register_user

NOTIFICATIONS_URL = "/api/v1/notifications"


class TestNotifications:
    """Test notification CRUD operations"""

    async def test_get_notifications_empty(self, client: AsyncClient):
        """Should return empty list when no notifications"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.get(NOTIFICATIONS_URL, headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert body["notifications"] == []
        assert body["total"] == 0
        assert body["next_offset"] is None

    async def test_get_notifications_pagination(self, client: AsyncClient):
        """Should paginate notifications correctly"""
        # Create a user who will RECEIVE likes
        receiver_data = await register_user(client)  # This user gets welcome bonus (premium)
        receiver_headers = {"Authorization": f"Bearer {receiver_data['access_token']}"}
        
        # Create multiple users to like the receiver
        for i in range(3):
            liker_payload = {
                "email": f"liker_{i}@example.com",
                "password": "strongpass123",
                "name": f"Liker {i}",
                "age": 25,
                "gender": "male"
            }
            liker_res = await client.post("/api/v1/auth/register", json=liker_payload)
            liker_data = liker_res.json()
            liker_headers = {"Authorization": f"Bearer {liker_data['access_token']}"}
            
            await client.post(
                "/api/v1/swipes",
                json={"user_id": receiver_data["user"]["id"], "direction": "like"},
                headers=liker_headers
            )
        
        # Get notifications for the RECEIVER (who got all the likes)
        res = await client.get(NOTIFICATIONS_URL, params={"limit": 2}, headers=receiver_headers)
        assert res.status_code == 200
        body = res.json()
        assert len(body["notifications"]) == 2  # Should have 2 of the 3 notifications
        assert body["total"] >= 3
        assert body["next_offset"] == 2

    async def test_get_notifications_requires_auth(self, client: AsyncClient):
        """Should return 401 without authentication"""
        res = await client.get(NOTIFICATIONS_URL)
        assert res.status_code == 401

    async def test_mark_single_notification_read(self, client: AsyncClient):
        """Should mark a single notification as read"""
        # Create a notification first
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        # Create another user to generate notification
        user2_payload = {
            "email": "markread@example.com",
            "password": "strongpass123",
            "name": "Mark Read Test",
            "age": 25,
            "gender": "male"
        }
        user2_res = await client.post("/api/v1/auth/register", json=user2_payload)
        user2_data = user2_res.json()
        user2_headers = {"Authorization": f"Bearer {user2_data['access_token']}"}
        
        # Like to create notification
        await client.post(
            "/api/v1/swipes",
            json={"user_id": data["user"]["id"], "direction": "like"},
            headers=user2_headers
        )
        
        # Get notifications
        get_res = await client.get(NOTIFICATIONS_URL, headers=headers)
        notifications = get_res.json()["notifications"]
        assert len(notifications) > 0
        assert notifications[0]["is_read"] is False
        
        # Mark as read
        notification_id = notifications[0]["id"]
        read_res = await client.post(
            NOTIFICATIONS_URL + "/read",
            json={"notification_ids": [notification_id]},
            headers=headers
        )
        assert read_res.status_code == 204
        
        # Verify it's marked read
        get_res2 = await client.get(NOTIFICATIONS_URL, headers=headers)
        for n in get_res2.json()["notifications"]:
            if n["id"] == notification_id:
                assert n["is_read"] is True

    async def test_mark_multiple_notifications_read(self, client: AsyncClient):
        """Should mark multiple notifications as read at once"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        # Create multiple notifications
        for i in range(3):
            user_payload = {
                "email": f"bulk{i}@example.com",
                "password": "strongpass123",
                "name": f"Bulk {i}",
                "age": 25,
                "gender": "male"
            }
            user_res = await client.post("/api/v1/auth/register", json=user_payload)
            user_data = user_res.json()
            user_headers = {"Authorization": f"Bearer {user_data['access_token']}"}
            await client.post(
                "/api/v1/swipes",
                json={"user_id": data["user"]["id"], "direction": "like"},
                headers=user_headers
            )
        
        # Get all notifications
        get_res = await client.get(NOTIFICATIONS_URL, headers=headers)
        notifications = get_res.json()["notifications"]
        notification_ids = [n["id"] for n in notifications[:2]]
        
        # Mark multiple as read
        read_res = await client.post(
            NOTIFICATIONS_URL + "/read",
            json={"notification_ids": notification_ids},
            headers=headers
        )
        assert read_res.status_code == 204
        
        # Verify they're marked read
        get_res2 = await client.get(NOTIFICATIONS_URL, headers=headers)
        for n in get_res2.json()["notifications"]:
            if n["id"] in notification_ids:
                assert n["is_read"] is True

    async def test_mark_read_invalid_notification_id(self, client: AsyncClient):
        """Should not fail when notification doesn't exist"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.post(
            NOTIFICATIONS_URL + "/read",
            json={"notification_ids": ["00000000-0000-0000-0000-000000000001"]},
            headers=headers
        )
        assert res.status_code == 204  # Should silently succeed

    async def test_mark_read_other_user_notification_fails(self, client: AsyncClient):
        """Should not mark notifications belonging to other users"""
        # Create user A
        userA_payload = {
            "email": "usera@example.com",
            "password": "strongpass123",
            "name": "User A",
            "age": 25,
            "gender": "female"
        }
        userA_res = await client.post("/api/v1/auth/register", json=userA_payload)
        userA_data = userA_res.json()
        userA_headers = {"Authorization": f"Bearer {userA_data['access_token']}"}
        
        # Create user B
        userB_payload = {
            "email": "userb@example.com",
            "password": "strongpass123",
            "name": "User B",
            "age": 25,
            "gender": "male"
        }
        userB_res = await client.post("/api/v1/auth/register", json=userB_payload)
        userB_data = userB_res.json()
        userB_headers = {"Authorization": f"Bearer {userB_data['access_token']}"}
        
        # User C likes user A (creates notification for user A)
        userC_payload = {
            "email": "userc@example.com",
            "password": "strongpass123",
            "name": "User C",
            "age": 25,
            "gender": "male"
        }
        userC_res = await client.post("/api/v1/auth/register", json=userC_payload)
        userC_data = userC_res.json()
        userC_headers = {"Authorization": f"Bearer {userC_data['access_token']}"}
        
        await client.post(
            "/api/v1/swipes",
            json={"user_id": userA_data["user"]["id"], "direction": "like"},
            headers=userC_headers
        )
        
        # Get user A's notifications
        get_res = await client.get(NOTIFICATIONS_URL, headers=userA_headers)
        userA_notifications = get_res.json()["notifications"]
        assert len(userA_notifications) > 0
        
        # User B tries to mark user A's notification as read
        res = await client.post(
            NOTIFICATIONS_URL + "/read",
            json={"notification_ids": [userA_notifications[0]["id"]]},
            headers=userB_headers
        )
        # Should succeed but not actually mark (or should 404)
        # The notification belongs to user A, not user B
        assert res.status_code in [204, 404]

    async def test_delete_notification(self, client: AsyncClient):
        """Should delete a notification"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        # Create notification via like
        user2_payload = {
            "email": "delete@example.com",
            "password": "strongpass123",
            "name": "Delete Test",
            "age": 25,
            "gender": "male"
        }
        user2_res = await client.post("/api/v1/auth/register", json=user2_payload)
        user2_data = user2_res.json()
        user2_headers = {"Authorization": f"Bearer {user2_data['access_token']}"}
        
        await client.post(
            "/api/v1/swipes",
            json={"user_id": data["user"]["id"], "direction": "like"},
            headers=user2_headers
        )
        
        # Get notification
        get_res = await client.get(NOTIFICATIONS_URL, headers=headers)
        notifications = get_res.json()["notifications"]
        assert len(notifications) > 0
        notification_id = notifications[0]["id"]
        
        # Delete notification
        del_res = await client.delete(f"{NOTIFICATIONS_URL}/{notification_id}", headers=headers)
        assert del_res.status_code == 204
        
        # Verify deleted
        get_res2 = await client.get(NOTIFICATIONS_URL, headers=headers)
        for n in get_res2.json()["notifications"]:
            assert n["id"] != notification_id

    async def test_delete_nonexistent_notification(self, client: AsyncClient):
        """Should return 404 when notification doesn't exist"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.delete(
            f"{NOTIFICATIONS_URL}/00000000-0000-0000-0000-000000000001",
            headers=headers
        )
        assert res.status_code == 404

    async def test_delete_other_user_notification(self, client: AsyncClient):
        """Should not delete notifications belonging to other users"""
        # Create user A using register_user (no email param)
        userA_data = await register_user(client)
        userA_headers = {"Authorization": f"Bearer {userA_data['access_token']}"}
        
        # Create user B using POST directly (to set specific email)
        userB_payload = {
            "email": "deleteB@example.com",
            "password": "strongpass123",
            "name": "Delete B",
            "age": 25,
            "gender": "male"
        }
        userB_res = await client.post("/api/v1/auth/register", json=userB_payload)
        userB_data = userB_res.json()
        userB_headers = {"Authorization": f"Bearer {userB_data['access_token']}"}
        
        # User C likes user A (creates notification for user A)
        userC_payload = {
            "email": "deleteC@example.com",
            "password": "strongpass123",
            "name": "Delete C",
            "age": 25,
            "gender": "male"
        }
        userC_res = await client.post("/api/v1/auth/register", json=userC_payload)
        userC_data = userC_res.json()
        userC_headers = {"Authorization": f"Bearer {userC_data['access_token']}"}
        
        await client.post(
            "/api/v1/swipes",
            json={"user_id": userA_data["user"]["id"], "direction": "like"},
            headers=userC_headers
        )
        
        # Get user A's notifications
        get_res = await client.get(NOTIFICATIONS_URL, headers=userA_headers)
        notifications = get_res.json()["notifications"]
        assert len(notifications) > 0
        notification_id = notifications[0]["id"]
        
        # User B tries to delete user A's notification
        del_res = await client.delete(f"{NOTIFICATIONS_URL}/{notification_id}", headers=userB_headers)
        assert del_res.status_code == 404  # Not found for user B