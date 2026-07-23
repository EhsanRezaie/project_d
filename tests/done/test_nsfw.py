# tests/done/test_nsfw.py
import io
import pytest
from PIL import Image
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.nsfw_service import NSFWService, nsfw_service
from app.schemas.nsfw import NSFWCheckResult, NSFWMetricsResponse, NSFWConfigResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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

    skin_height = int(size[1] * ratio)
    for y in range(skin_height):
        for x in range(size[0]):
            img.putpixel((x, y), skin_color)

    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return buf.getvalue()


async def _register_user(client, email):
    """Register a user via 3-step flow and return access_token."""
    # Step 1: init (generates code in Redis)
    res = await client.post("/api/v1/auth/register/init", json={"email": email})
    assert res.status_code == 200, res.text

    # Step 2: verify — store code AFTER init overwrites it
    from app.core.redis import redis_client
    await redis_client.set(f"verification:{email}", "123456")

    res = await client.post("/api/v1/auth/register/verify", json={
        "email": email, "code": "123456", "password": "testpass123",
    })
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]

    # Step 3: complete profile
    res = await client.post("/api/v1/auth/register/complete", json={
        "name": "NSFW Test User",
        "birth_date": "2000-01-01",
        "gender": "male",
        "lat": 35.6892,
        "lng": 51.3890,
        "sexual_orientation": "straight",
        "bio": "Test",
        "height": 180,
        "weight": 75,
        "body_type": "athletic",
        "relationship_status": "single",
        "living_situation": "alone",
        "children_status": "dont_have",
        "smoking": "never",
        "drinking": "socially",
        "education": "bachelor",
        "workplace": "Tech",
        "religion": "islam",
        "ethnicity": "persian",
        "political_orientation": "moderate",
        "languages": ["persian", "english"],
        "country": "Iran",
        "province": "Tehran",
        "city": "Tehran",
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200, res.text
    return token


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

class TestNSFWSchemas:

    def test_check_result_schema(self):
        result = NSFWCheckResult(is_safe=True, score=0.2, threshold=0.8)
        assert result.is_safe is True
        assert result.score == 0.2
        assert result.threshold == 0.8

    def test_metrics_response_schema(self):
        metrics = NSFWMetricsResponse(
            total_checked=10, total_rejected=2, reject_rate=0.2,
            enabled=True, threshold=0.8,
        )
        assert metrics.total_checked == 10
        assert metrics.reject_rate == 0.2

    def test_config_response_schema(self):
        config = NSFWConfigResponse(enabled=True, threshold=0.8)
        assert config.enabled is True
        assert config.threshold == 0.8


# ---------------------------------------------------------------------------
# NSFWService unit tests
# ---------------------------------------------------------------------------

class TestNSFWService:

    def test_init_default(self):
        service = NSFWService()
        assert service.threshold == 0.8
        assert service.enabled is True

    def test_metrics_initial(self):
        service = NSFWService()
        metrics = service.get_metrics()
        assert metrics["total_checked"] == 0
        assert metrics["total_rejected"] == 0
        assert metrics["reject_rate"] == 0.0

    def test_classify_safe_image(self):
        service = NSFWService()
        img_bytes = _make_image(color=(50, 100, 150))  # blue-ish, low skin
        score = service._classify_heuristic(img_bytes)
        assert score < 0.5

    def test_classify_skin_heavy_image(self):
        service = NSFWService()
        img_bytes = _make_skin_image(ratio=0.7)
        score = service._classify_heuristic(img_bytes)
        assert score > 0.5

    def test_score_range(self):
        service = NSFWService()
        score_safe = service._classify_heuristic(_make_image(color=(50, 100, 150)))
        score_nsfw = service._classify_heuristic(_make_skin_image(ratio=0.9))
        assert 0.0 <= score_safe <= 1.0
        assert 0.0 <= score_nsfw <= 1.0
        assert score_nsfw > score_safe

    @pytest.mark.asyncio
    async def test_disabled_service_always_safe(self):
        service = NSFWService()
        service._enabled = False
        is_safe, score = await service.check_image(_make_image())
        assert bool(is_safe) is True
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_fail_open_on_error(self):
        service = NSFWService()
        is_safe, score = await service.check_image(b"not an image")
        assert bool(is_safe) is True
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_check_image_safe(self):
        service = NSFWService()
        service._threshold = 0.8
        img_bytes = _make_image(color=(50, 100, 150))
        is_safe, score = await service.check_image(img_bytes)
        assert bool(is_safe) is True
        assert score < 0.8

    @pytest.mark.asyncio
    async def test_check_image_reject(self):
        service = NSFWService()
        service._threshold = 0.3  # Low threshold to trigger rejection
        img_bytes = _make_skin_image(ratio=0.8)
        is_safe, score = await service.check_image(img_bytes)
        assert bool(is_safe) is False
        assert score >= 0.3

    @pytest.mark.asyncio
    async def test_metrics_tracking(self):
        service = NSFWService()
        service._threshold = 0.3  # Low threshold to trigger rejection

        await service.check_image(_make_image(color=(50, 100, 150)))  # safe
        await service.check_image(_make_skin_image(ratio=0.8))  # rejected

        metrics = service.get_metrics()
        assert metrics["total_checked"] == 2
        assert metrics["total_rejected"] >= 1

    @pytest.mark.asyncio
    async def test_quarantine_photo(self):
        service = NSFWService()
        img_bytes = _make_image()

        key = await service.quarantine_photo(img_bytes, "user-123", "photo-456")
        assert key == "quarantine/user-123/photo-456.jpg"


# ---------------------------------------------------------------------------
# Endpoint integration tests
# ---------------------------------------------------------------------------

class TestNSFWEndpoint:

    async def test_upload_safe_photo(self, client, mock_verification_code):
        """Should accept safe photo."""
        token = await _register_user(client, "nsfw_safe@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        img_bytes = _make_image(color=(50, 100, 150))
        res = await client.post(
            "/api/v1/users/me/photos",
            headers=headers,
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "pending"

    async def test_upload_rejects_nsfw_content(self, client, mock_verification_code):
        """Should reject NSFW content when nsfw_service says not safe."""
        token = await _register_user(client, "nsfw_reject@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.api.v1.endpoints.photos.nsfw_service") as mock_nsfw:
            mock_nsfw.check_image = AsyncMock(return_value=(False, 0.95))
            mock_nsfw.quarantine_photo = AsyncMock(return_value="quarantine/test.jpg")

            img_bytes = _make_skin_image(ratio=0.9)
            res = await client.post(
                "/api/v1/users/me/photos",
                headers=headers,
                files={"file": ("nsfw.jpg", img_bytes, "image/jpeg")},
            )
            assert res.status_code == 400
            assert "content policy" in res.json()["detail"].lower()
            mock_nsfw.quarantine_photo.assert_called_once()

    async def test_upload_invalid_format(self, client, mock_verification_code):
        """Should reject invalid image format."""
        token = await _register_user(client, "nsfw_invalid@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        res = await client.post(
            "/api/v1/users/me/photos",
            headers=headers,
            files={"file": ("test.txt", b"not an image", "text/plain")},
        )
        assert res.status_code == 400

    async def test_nsfw_score_saved_to_photo(self, client, mock_verification_code):
        """NSFW score should be stored on the photo record."""
        token = await _register_user(client, "nsfw_score@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.api.v1.endpoints.photos.nsfw_service") as mock_nsfw:
            mock_nsfw.check_image = AsyncMock(return_value=(True, 0.15))

            img_bytes = _make_image(color=(50, 100, 150))
            res = await client.post(
                "/api/v1/users/me/photos",
                headers=headers,
                files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            )
            assert res.status_code == 201

            # Verify the score was saved
            res = await client.get("/api/v1/users/me/photos", headers=headers)
            assert res.status_code == 200
            photos = res.json()
            assert len(photos) >= 1

    async def test_nsfw_disabled_bypasses_check(self, client, mock_verification_code):
        """When NSFW is disabled, all images should pass."""
        token = await _register_user(client, "nsfw_disabled@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.api.v1.endpoints.photos.nsfw_service") as mock_nsfw:
            mock_nsfw.check_image = AsyncMock(return_value=(True, 0.0))

            img_bytes = _make_skin_image(ratio=0.9)
            res = await client.post(
                "/api/v1/users/me/photos",
                headers=headers,
                files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            )
            assert res.status_code == 201


# ---------------------------------------------------------------------------
# Singleton / global service tests
# ---------------------------------------------------------------------------

class TestNSFWMetrics:

    def test_singleton_has_metrics(self):
        metrics = nsfw_service.get_metrics()
        assert "total_checked" in metrics
        assert "total_rejected" in metrics
        assert "reject_rate" in metrics

    def test_singleton_has_config(self):
        assert hasattr(nsfw_service, "threshold")
        assert hasattr(nsfw_service, "enabled")
        assert isinstance(nsfw_service.threshold, float)
        assert isinstance(nsfw_service.enabled, bool)
