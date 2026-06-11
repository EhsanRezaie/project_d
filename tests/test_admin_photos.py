import pytest
from httpx import AsyncClient
from tests.test_auth import register_user
from PIL import Image
import io
from app.core.config import settings

ADMIN_PHOTOS_URL = "/api/v1/admin/photos"
ADMIN_KEY = settings.ADMIN_SECRET_KEY


class TestAdminPhotos:
    """Test admin photo moderation"""

    async def create_test_photo(self, client, headers):
        """Helper to create a test photo"""
        # Create a simple test image
        img = Image.new('RGB', (200, 200), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
        
        return await client.post(
            "/api/v1/users/me/photos",
            files=files,
            headers=headers
        )

    async def test_admin_get_pending_photos(self, client: AsyncClient):
        """Admin should list pending photos"""
        # Upload a photo (status = pending)
        user_data = await register_user(client)
        user_headers = {"Authorization": f"Bearer {user_data['access_token']}"}
        await self.create_test_photo(client, user_headers)
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(f"{ADMIN_PHOTOS_URL}/pending", headers=admin_headers)
        assert res.status_code == 200
        body = res.json()
        assert len(body) >= 1

    async def test_admin_approve_photo(self, client: AsyncClient):
        """Admin should approve a pending photo"""
        # Upload a photo
        user_data = await register_user(client)
        user_headers = {"Authorization": f"Bearer {user_data['access_token']}"}
        upload_res = await self.create_test_photo(client, user_headers)
        photo_id = upload_res.json()["id"]
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.post(
            f"{ADMIN_PHOTOS_URL}/{photo_id}/approve",
            headers=admin_headers
        )
        assert res.status_code == 200
        assert res.json()["message"] == "Photo approved successfully"

    async def test_admin_reject_photo(self, client: AsyncClient):
        """Admin should reject a pending photo with reason"""
        # Upload a photo
        user_data = await register_user(client)
        user_headers = {"Authorization": f"Bearer {user_data['access_token']}"}
        upload_res = await self.create_test_photo(client, user_headers)
        photo_id = upload_res.json()["id"]
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.post(
            f"{ADMIN_PHOTOS_URL}/{photo_id}/reject",
            params={"reason": "Inappropriate content"},
            headers=admin_headers
        )
        assert res.status_code == 200
        assert res.json()["message"] == "Photo rejected successfully"
        assert res.json()["reason"] == "Inappropriate content"

    async def test_admin_photo_stats(self, client: AsyncClient):
        """Admin should get photo moderation statistics"""
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(f"{ADMIN_PHOTOS_URL}/stats", headers=admin_headers)
        assert res.status_code == 200
        body = res.json()
        
        assert "pending" in body
        assert "approved" in body
        assert "rejected" in body
        assert "total" in body

    async def test_admin_get_photo_detail(self, client: AsyncClient):
        """Admin should get photo details with user info"""
        # Upload a photo
        user_data = await register_user(client)
        user_headers = {"Authorization": f"Bearer {user_data['access_token']}"}
        upload_res = await self.create_test_photo(client, user_headers)
        photo_id = upload_res.json()["id"]
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(f"{ADMIN_PHOTOS_URL}/{photo_id}", headers=admin_headers)
        assert res.status_code == 200
        body = res.json()
        
        assert body["id"] == photo_id
        assert "user_id" in body
        assert "user_name" in body
        assert "url" in body
        assert "status" in body

    async def test_admin_verify_face(self, client: AsyncClient):
        """Admin should mark photo as face-verified"""
        # Upload a photo
        user_data = await register_user(client)
        user_headers = {"Authorization": f"Bearer {user_data['access_token']}"}
        upload_res = await self.create_test_photo(client, user_headers)
        photo_id = upload_res.json()["id"]
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.post(
            f"{ADMIN_PHOTOS_URL}/{photo_id}/verify-face",
            headers=admin_headers
        )
        assert res.status_code == 200
        assert res.json()["face_verified"] is True

    async def test_admin_get_user_photos(self, client: AsyncClient):
        """Admin should get all photos for a specific user"""
        # Upload photos
        user_data = await register_user(client)
        user_headers = {"Authorization": f"Bearer {user_data['access_token']}"}
        await self.create_test_photo(client, user_headers)
        await self.create_test_photo(client, user_headers)
        
        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(
            f"{ADMIN_PHOTOS_URL}/users/{user_data['user']['id']}/photos",
            headers=admin_headers
        )
        assert res.status_code == 200
        body = res.json()
        assert len(body) >= 2

    async def test_admin_photos_requires_admin_key(self, client: AsyncClient):
        """Should return 401 with wrong admin key"""
        # Create a normal user (not admin)
        user_data = await register_user(client)

        # Try to access admin endpoint with valid JWT + WRONG admin key
        wrong_headers = {
            "X-Admin-Key": "WRONG_KEY_123"
        }
        res = await client.get(f"{ADMIN_PHOTOS_URL}/pending", headers=wrong_headers)
        assert res.status_code == 403
        assert "Admin access required" in res.json()["detail"]