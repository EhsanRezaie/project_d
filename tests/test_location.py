import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from tests.test_auth import register_user

LOCATIONS_PROVINCES_URL = "/api/v1/locations/provinces"
LOCATIONS_CITIES_URL = "/api/v1/locations/cities"
LOCATIONS_VALIDATE_URL = "/api/v1/locations/validate"
LOCATION_TEXT_URL = "/api/v1/users/me/location-text"
LOCATION_URL = "/api/v1/users/me/location"


class TestLocationEndpoints:
    """Test location API endpoints"""

    async def test_get_provinces_success(self, client: AsyncClient):
        """Should return list of Iranian provinces"""
        res = await client.get(LOCATIONS_PROVINCES_URL)
        assert res.status_code == 200
        body = res.json()
        
        assert body["country"] == "Iran"
        assert body["country_code"] == "IR"
        assert "provinces" in body
        assert len(body["provinces"]) > 0
        
        # Verify Tehran exists
        tehran = next((p for p in body["provinces"] if p["name"] == "Tehran"), None)
        assert tehran is not None
        assert tehran["code"] == "23"

    async def test_get_cities_by_province_code(self, client: AsyncClient):
        """Should return cities for Tehran province"""
        # Tehran province code is "23"
        res = await client.get(LOCATIONS_CITIES_URL, params={"province_code": "23"})
        assert res.status_code == 200
        body = res.json()
        
        assert body["province_code"] == "23"
        assert "cities" in body
        assert len(body["cities"]) > 0
        
        # Verify Tehran city exists
        tehran_city = next((c for c in body["cities"] if c["name"] == "Tehran"), None)
        assert tehran_city is not None

    async def test_get_cities_invalid_province_code(self, client: AsyncClient):
        """Should return 404 for invalid province code"""
        res = await client.get(LOCATIONS_CITIES_URL, params={"province_code": "INVALID"})
        assert res.status_code == 404
        assert "Province with code 'INVALID' not found" in res.json()["detail"]

    async def test_get_cities_missing_province_code(self, client: AsyncClient):
        """Should return 422 when province_code is missing"""
        res = await client.get(LOCATIONS_CITIES_URL)
        assert res.status_code == 422

    async def test_validate_valid_province(self, client: AsyncClient):
        """Should validate a valid province (using name)"""
        res = await client.get(LOCATIONS_VALIDATE_URL, params={"province": "Tehran"})
        assert res.status_code == 200
        body = res.json()
        
        assert body["valid"] is True
        assert body["province"]["name"] == "Tehran"
        assert body["province"]["code"] == "23"

    async def test_validate_valid_province_and_city(self, client: AsyncClient):
        """Should validate a valid province and city"""
        res = await client.get(
            LOCATIONS_VALIDATE_URL, 
            params={"province": "Tehran", "city": "Tehran"}
        )
        assert res.status_code == 200
        body = res.json()
        
        assert body["valid"] is True
        assert body["province"]["name"] == "Tehran"
        assert body["province"]["code"] == "23"
        assert body["city"]["name"] == "Tehran"

    async def test_validate_invalid_province(self, client: AsyncClient):
        """Should return 400 for invalid province"""
        res = await client.get(LOCATIONS_VALIDATE_URL, params={"province": "InvalidProvince"})
        assert res.status_code == 400
        assert "Province 'InvalidProvince' not found" in res.json()["detail"]

    async def test_validate_invalid_city(self, client: AsyncClient):
        """Should return 400 for invalid city in valid province"""
        res = await client.get(
            LOCATIONS_VALIDATE_URL,
            params={"province": "Tehran", "city": "InvalidCity"}
        )
        assert res.status_code == 400
        assert "City 'InvalidCity' not found" in res.json()["detail"]

    async def test_validate_case_insensitive(self, client: AsyncClient):
        """Should be case-insensitive for province names"""
        res = await client.get(LOCATIONS_VALIDATE_URL, params={"province": "TEHRAN"})
        assert res.status_code == 200
        assert res.json()["valid"] is True


class TestUserLocationText:
    """Test user location text update"""

    async def test_update_location_text_success(self, client: AsyncClient):
        """Should update user's location with valid province and city"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.patch(
            LOCATION_TEXT_URL,
            json={"country": "Iran", "province": "Tehran", "city": "Tehran"},
            headers=headers
        )
        assert res.status_code == 200
        body = res.json()
        
        assert body["country"] == "Iran"
        assert body["province"] == "Tehran"
        assert body["city"] == "Tehran"
        assert body["location_manual"] is True

    async def test_update_location_without_city(self, client: AsyncClient):
        """Should update province without city"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.patch(
            LOCATION_TEXT_URL,
            json={"country": "Iran", "province": "Isfahan"},
            headers=headers
        )
        assert res.status_code == 200
        body = res.json()
        
        assert body["country"] == "Iran"
        assert body["province"] == "Isfahan"

    async def test_update_location_invalid_province(self, client: AsyncClient):
        """Should reject invalid province"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.patch(
            LOCATION_TEXT_URL,
            json={"country": "Iran", "province": "InvalidProvince"},
            headers=headers
        )
        assert res.status_code == 400
        assert "Province 'InvalidProvince' not found" in res.json()["detail"]

    async def test_update_location_invalid_city(self, client: AsyncClient):
        """Should reject invalid city for valid province"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.patch(
            LOCATION_TEXT_URL,
            json={"country": "Iran", "province": "Tehran", "city": "InvalidCity"},
            headers=headers
        )
        assert res.status_code == 400
        assert "City 'InvalidCity' not found" in res.json()["detail"]

    async def test_update_location_partial_update(self, client: AsyncClient):
        """Should allow partial update (only city)"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        # First set province
        await client.patch(
            LOCATION_TEXT_URL,
            json={"province": "Tehran"},
            headers=headers
        )
        
        # Then update city only
        res = await client.patch(
            LOCATION_TEXT_URL,
            json={"city": "Tehran"},
            headers=headers
        )
        assert res.status_code == 200
        body = res.json()
        assert body["province"] == "Tehran"
        assert body["city"] == "Tehran"

    async def test_update_location_requires_auth(self, client: AsyncClient):
        """Should return 401 without authentication"""
        res = await client.patch(
            LOCATION_TEXT_URL,
            json={"country": "Iran", "province": "Tehran"}
        )
        assert res.status_code == 401

    async def test_location_appears_in_profile(self, client: AsyncClient):
        """Should see location fields in user profile after update"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.patch(
            LOCATION_TEXT_URL,
            json={"country": "Iran", "province": "Fars", "city": "Shiraz"},
            headers=headers
        )
        assert res.status_code == 200
        
        # Get profile
        res = await client.get("/api/v1/users/me", headers=headers)
        assert res.status_code == 200
        body = res.json()
        
        assert body.get("country") == "Iran"
        assert body.get("province") == "Fars"
        assert body.get("city") == "Shiraz"

    async def test_search_by_province(self, client: AsyncClient):
        """Should search users by province"""
        user1_data = await register_user(client)
        user1_headers = {"Authorization": f"Bearer {user1_data['access_token']}"}
        await client.patch(
            LOCATION_TEXT_URL,
            json={"province": "Tehran"},
            headers=user1_headers
        )
        
        user2_payload = {
            "email": "searcher@example.com",
            "password": "strongpass123",
            "name": "Searcher",
            "age": 25,
            "gender": "female"
        }
        user2_res = await client.post("/api/v1/auth/register", json=user2_payload)
        user2_headers = {"Authorization": f"Bearer {user2_res.json()['access_token']}"}
        
        res = await client.get(
            "/api/v1/search",
            params={"province": "Tehran"},
            headers=user2_headers
        )
        assert res.status_code == 200
        body = res.json()
        
        users = body.get("users", [])
        found = any(u.get("id") == str(user1_data["user"]["id"]) for u in users)
        assert found is True

    async def test_search_by_city(self, client: AsyncClient):
        """Should search users by city"""
        user1_data = await register_user(client)
        user1_headers = {"Authorization": f"Bearer {user1_data['access_token']}"}
        await client.patch(
            LOCATION_TEXT_URL,
            json={"province": "Fars", "city": "Shiraz"},
            headers=user1_headers
        )
        
        user2_payload = {
            "email": "city_searcher@example.com",
            "password": "strongpass123",
            "name": "City Searcher",
            "age": 25,
            "gender": "female"
        }
        user2_res = await client.post("/api/v1/auth/register", json=user2_payload)
        user2_headers = {"Authorization": f"Bearer {user2_res.json()['access_token']}"}
        
        res = await client.get(
            "/api/v1/search",
            params={"city": "Shiraz"},
            headers=user2_headers
        )
        assert res.status_code == 200
        body = res.json()
        
        users = body.get("users", [])
        found = any(u.get("id") == str(user1_data["user"]["id"]) for u in users)
        assert found is True


class TestReverseGeocoding:
    """Test auto-fill location from GPS coordinates"""

    async def test_update_location_auto_fills_country_province_city(self, client: AsyncClient):
        """When user sends lat/lng, should auto-fill country/province/city from reverse geocoding"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        mock_location_data = {
            "country": "Iran",
            "province": "Tehran",
            "city": "Tehran"
        }
        
        with patch("app.services.location_service.LocationService.reverse_geocode", new_callable=AsyncMock) as mock_geocode:
            mock_geocode.return_value = mock_location_data
            
            res = await client.post(
                LOCATION_URL,
                params={"lat": 35.6892, "lng": 51.3890},
                headers=headers
            )
            assert res.status_code == 204
            
            mock_geocode.assert_called_once_with(35.6892, 51.3890)
            
            profile_res = await client.get("/api/v1/users/me", headers=headers)
            assert profile_res.status_code == 200
            profile = profile_res.json()
            
            assert profile["lat"] == 35.6892
            assert profile["lng"] == 51.3890
            assert profile["country"] == "Iran"
            assert profile["province"] == "Tehran"
            assert profile["city"] == "Tehran"
            assert profile["location_manual"] is False

    async def test_update_location_does_not_auto_fill_if_manual_true(self, client: AsyncClient):
        """If user already manually set location, don't auto-fill from coordinates"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        await client.patch(
            LOCATION_TEXT_URL,
            json={"country": "Iran", "province": "Isfahan", "city": "Isfahan"},
            headers=headers
        )
        
        with patch("app.services.location_service.LocationService.reverse_geocode", new_callable=AsyncMock) as mock_geocode:
            res = await client.post(
                LOCATION_URL,
                params={"lat": 35.6892, "lng": 51.3890},
                headers=headers
            )
            assert res.status_code == 204
            
            mock_geocode.assert_not_called()
            
            profile_res = await client.get("/api/v1/users/me", headers=headers)
            profile = profile_res.json()
            
            assert profile["lat"] == 35.6892
            assert profile["lng"] == 51.3890
            assert profile["country"] == "Iran"
            assert profile["province"] == "Isfahan"
            assert profile["city"] == "Isfahan"
            assert profile["location_manual"] is True

    async def test_update_location_handles_geocoding_failure(self, client: AsyncClient):
        """If reverse geocoding fails, still save lat/lng but don't set text fields"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        with patch("app.services.location_service.LocationService.reverse_geocode", new_callable=AsyncMock) as mock_geocode:
            mock_geocode.return_value = None
            
            res = await client.post(
                LOCATION_URL,
                params={"lat": 35.6892, "lng": 51.3890},
                headers=headers
            )
            assert res.status_code == 204
            
            mock_geocode.assert_called_once()
            
            profile_res = await client.get("/api/v1/users/me", headers=headers)
            profile = profile_res.json()
            
            assert profile["lat"] == 35.6892
            assert profile["lng"] == 51.3890
            assert profile["country"] is None
            assert profile["province"] is None
            assert profile["city"] is None
            assert profile["location_manual"] is False

    async def test_update_location_requires_valid_coordinates(self, client: AsyncClient):
        """Should reject invalid lat/lng values"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        res = await client.post(
            LOCATION_URL,
            params={"lat": 100, "lng": 51.3890},
            headers=headers
        )
        assert res.status_code == 400
        assert "Latitude must be between -90 and 90" in res.json()["detail"]
        
        res = await client.post(
            LOCATION_URL,
            params={"lat": 35.6892, "lng": 200},
            headers=headers
        )
        assert res.status_code == 400
        assert "Longitude must be between -180 and 180" in res.json()["detail"]

    async def test_update_location_updates_last_seen(self, client: AsyncClient):
        """Should update last_seen_at when location is updated"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        profile_before = await client.get("/api/v1/users/me", headers=headers)
        last_seen_before = profile_before.json().get("last_seen_at")
        
        with patch("app.services.location_service.LocationService.reverse_geocode", new_callable=AsyncMock) as mock_geocode:
            mock_geocode.return_value = None
            
            await client.post(
                LOCATION_URL,
                params={"lat": 35.6892, "lng": 51.3890},
                headers=headers
            )
        
        profile_after = await client.get("/api/v1/users/me", headers=headers)
        last_seen_after = profile_after.json().get("last_seen_at")
        
        assert last_seen_after is not None
        if last_seen_before:
            assert last_seen_after != last_seen_before


class TestLocationManualVsAuto:
    """Test interaction between manual and auto location"""

    async def test_manual_location_overrides_auto(self, client: AsyncClient):
        """Setting manual location should set location_manual=True and prevent auto updates"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        # First, auto-fill from GPS
        with patch("app.services.location_service.LocationService.reverse_geocode", new_callable=AsyncMock) as mock_geocode:
            mock_geocode.return_value = {"country": "Iran", "province": "Tehran", "city": "Tehran"}
            await client.post(LOCATION_URL, params={"lat": 35.6892, "lng": 51.3890}, headers=headers)
        
        profile = await client.get("/api/v1/users/me", headers=headers)
        assert profile.json()["location_manual"] is False
        assert profile.json()["province"] == "Tehran"
        
        # Then manually update
        await client.patch(
            LOCATION_TEXT_URL,
            json={"province": "Fars", "city": "Shiraz"},
            headers=headers
        )
        
        profile2 = await client.get("/api/v1/users/me", headers=headers)
        assert profile2.json()["location_manual"] is True
        assert profile2.json()["province"] == "Fars"
        assert profile2.json()["city"] == "Shiraz"
        
        # Subsequent GPS updates should not change text location
        with patch("app.services.location_service.LocationService.reverse_geocode", new_callable=AsyncMock) as mock_geocode:
            mock_geocode.return_value = {"country": "Iran", "province": "Tehran", "city": "Tehran"}
            await client.post(LOCATION_URL, params={"lat": 35.6892, "lng": 51.3890}, headers=headers)
        
        profile3 = await client.get("/api/v1/users/me", headers=headers)
        assert profile3.json()["location_manual"] is True
        assert profile3.json()["province"] == "Fars"
        assert profile3.json()["city"] == "Shiraz"

    async def test_partial_location_update(self, client: AsyncClient):
        """Can update only province without affecting other fields"""
        data = await register_user(client)
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        await client.patch(
            LOCATION_TEXT_URL,
            json={"country": "Iran", "province": "Tehran", "city": "Tehran"},
            headers=headers
        )
        
        await client.patch(
            LOCATION_TEXT_URL,
            json={"province": "Isfahan"},
            headers=headers
        )
        
        profile = await client.get("/api/v1/users/me", headers=headers)
        assert profile.json()["country"] == "Iran"
        assert profile.json()["province"] == "Isfahan"
        assert profile.json()["city"] == "Tehran"