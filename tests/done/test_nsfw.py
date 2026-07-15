# tests/done/test_nsfw.py
import io
import pytest
from PIL import Image
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.nsfw_service import NSFWService, nsfw_service


def _make_image(color=(100, 150, 200), size=(300, 300)) -> bytes:
    """Create a test image and return as bytes."""
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return buf.getvalue()


def _make_skin_image(ratio=0.5, size=(300, 300)) -> bytes:
    """Create an image with a specified ratio of skin-colored pixels."""
    img = Image.new("RGB", size, (100, 100, 100))  # dark background
    skin_color = (200, 160, 120)  # approximate skin tone in RGB

    # Fill top portion with skin color
    skin_height = int(size[1] * ratio)
    for y in range(skin_height):
        for x in range(size[0]):
            img.putpixel((x, y), skin_color)

    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return buf.getvalue()


class TestNSFWService:

    def test_init_default(self):
        """Should initialize with default settings."""
        service = NSFWService()
        assert service.threshold == 0.8
        assert service.enabled is True

    def test_metrics_initial(self):
        """Should start with zero metrics."""
        service = NSFWService()
        metrics = service.get_metrics()
        assert metrics["total_checked"] == 0
        assert metrics["total_rejected"] == 0
        assert metrics["reject_rate"] == 0.0

    def test_classify_safe_image(self):
        """Safe image (low skin ratio) should have low score."""
        service = NSFWService()
        img_bytes = _make_image(color=(50, 100, 150))  # blue-ish, low skin
        score = service._classify_heuristic(img_bytes)
        assert score < 0.5

    def test_classify_skin_heavy_image(self):
        """Image with high skin ratio should have higher score."""
        service = NSFWService()
        img_bytes = _make_skin_image(ratio=0.7)
        score = service._classify_heuristic(img_bytes)
        assert score > 0.5

    def test_disabled_service_always_safe(self):
        """When disabled, all images should pass."""
        service = NSFWService()
        service._enabled = False
        import asyncio
        is_safe, score = asyncio.run(service.check_image(_make_image()))
        assert is_safe is True
        assert score == 0.0

    def test_fail_open_on_error(self):
        """Should fail open (allow) on processing errors."""
        service = NSFWService()
        import asyncio
        is_safe, score = asyncio.run(service.check_image(b"not an image"))
        assert is_safe is True
        assert score == 0.0

    def test_metrics_tracking(self):
        """Should track check and rejection counts."""
        service = NSFWService()
        service._threshold = 0.3  # Low threshold to trigger rejection

        import asyncio
        # Safe image
        asyncio.run(service.check_image(_make_image(color=(50, 100, 150))))
        # Skin-heavy image
        asyncio.run(service.check_image(_make_skin_image(ratio=0.8)))

        metrics = service.get_metrics()
        assert metrics["total_checked"] == 2
        assert metrics["total_rejected"] >= 1


class TestNSFWEndpoint:

    async def test_upload_safe_photo(self, client, mock_verification_code):
        """Should accept safe photo."""
        from tests.done.test_push_notifications import (
            register_user, COMPLETE_PROFILE_PAYLOAD, VALID_EMAIL, VALID_PASSWORD
        )
        result = await register_user(client, VALID_EMAIL, COMPLETE_PROFILE_PAYLOAD, mock_verification_code)
        headers = {"Authorization": f"Bearer {result['access_token']}"}

        img_bytes = _make_image(color=(50, 100, 150))
        res = await client.post(
            "/api/v1/users/me/photos",
            headers=headers,
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
        )
        assert res.status_code == 201

    async def test_upload_invalid_format(self, client, mock_verification_code):
        """Should reject invalid image format."""
        from tests.done.test_push_notifications import (
            register_user, COMPLETE_PROFILE_PAYLOAD, VALID_EMAIL
        )
        result = await register_user(client, VALID_EMAIL, COMPLETE_PROFILE_PAYLOAD, mock_verification_code)
        headers = {"Authorization": f"Bearer {result['access_token']}"}

        res = await client.post(
            "/api/v1/users/me/photos",
            headers=headers,
            files={"file": ("test.txt", b"not an image", "text/plain")},
        )
        assert res.status_code == 400


class TestNSFWMetrics:

    def test_singleton_has_metrics(self):
        """Global nsfw_service should expose metrics."""
        metrics = nsfw_service.get_metrics()
        assert "total_checked" in metrics
        assert "total_rejected" in metrics
        assert "reject_rate" in metrics
