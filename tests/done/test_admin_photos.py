import pytest
from httpx import AsyncClient
from PIL import Image
import io
from app.core.config import settings

REGISTER_INIT_URL = "/api/v1/auth/register/init"
REGISTER_VERIFY_URL = "/api/v1/auth/register/verify"
REGISTER_COMPLETE_URL = "/api/v1/auth/register/complete"
ADMIN_PHOTOS_URL = "/api/v1/admin/photos"
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


async def register_user(client: AsyncClient, email: str = "photo@example.com", mock_verification_code=None) -> dict:
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

    async def test_admin_get_pending_photos(self, client: AsyncClient, mock_verification_code):
        """Admin should list pending photos"""
        # Upload a photo (status = pending)
        user_data = await register_user(client, "photopending@example.com", mock_verification_code)
        user_headers = {"Authorization": f"Bearer {user_data['access_token']}"}
        await self.create_test_photo(client, user_headers)

        admin_headers = {"X-Admin-Key": ADMIN_KEY}
        res = await client.get(f"{ADMIN_PHOTOS_URL}/pending", headers=admin_headers)
        assert res.status_code == 200
        body = res.json()
        assert len(body) >= 1

    async def test_admin_approve_photo(self, client: AsyncClient, mock_verification_code):
        """Admin should approve a pending photo"""
        # Upload a photo
        user_data = await register_user(client, "photoapprove@example.com", mock_verification_code)
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

    async def test_admin_reject_photo(self, client: AsyncClient, mock_verification_code):
        """Admin should reject a pending photo with reason"""
        # Upload a photo
        user_data = await register_user(client, "photoreject@example.com", mock_verification_code)
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

    async def test_admin_get_photo_detail(self, client: AsyncClient, mock_verification_code):
        """Admin should get photo details with user info"""
        # Upload a photo
        user_data = await register_user(client, "photodetail@example.com", mock_verification_code)
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

    async def test_admin_verify_face(self, client: AsyncClient, mock_verification_code):
        """Admin should mark photo as face-verified"""
        # Upload a photo
        user_data = await register_user(client, "faceverify@example.com", mock_verification_code)
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

    async def test_admin_get_user_photos(self, client: AsyncClient, mock_verification_code):
        """Admin should get all photos for a specific user"""
        # Upload photos
        user_data = await register_user(client, "userphotos@example.com", mock_verification_code)
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

    async def test_admin_photos_requires_admin_key(self, client: AsyncClient, mock_verification_code):
        """Should return 401 with wrong admin key"""
        # Create a normal user (not admin)
        user_data = await register_user(client, "photoauth@example.com", mock_verification_code)

        # Try to access admin endpoint with valid JWT + WRONG admin key
        wrong_headers = {
            "X-Admin-Key": "WRONG_KEY_123"
        }
        res = await client.get(f"{ADMIN_PHOTOS_URL}/pending", headers=wrong_headers)
        assert res.status_code == 403
        assert "Admin access required" in res.json()["detail"]
