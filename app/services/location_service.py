# app/services/location_service.py
"""
Global location service: countries, provinces, cities, reverse geocoding.
"""
import json
import httpx
import pycountry
import geonamescache
from functools import lru_cache
from typing import Optional, List, Dict, Any, Tuple

from app.core.logging import get_logger

logger = get_logger("location_service")

_gc = geonamescache.GeonamesCache()

REVERSE_GC_CACHE_TTL = 60 * 60 * 24
NOMINATIM_USER_AGENT = "DatingApp/1.0"


@lru_cache(maxsize=1)
def _countries_cached() -> list[dict]:
    gc_countries = _gc.get_countries()
    result = []
    for country in pycountry.countries:
        gc = gc_countries.get(country.alpha_2, {})
        result.append({
            "iso2": country.alpha_2,
            "iso3": country.alpha_3,
            "name": country.name,
            "latitude": gc.get("latitude"),
            "longitude": gc.get("longitude"),
        })
    return sorted(result, key=lambda c: c["name"])


def get_countries() -> list[dict]:
    return _countries_cached()


def get_country_by_iso2(iso2: str) -> Optional[dict]:
    iso2 = iso2.upper()
    for c in get_countries():
        if c["iso2"] == iso2:
            return c
    return None


@lru_cache(maxsize=256)
def _provinces_cached(country_iso2: str) -> list[dict]:
    subdivisions = pycountry.subdivisions.get(country_code=country_iso2)
    if not subdivisions:
        return []
    result = []
    for sub in subdivisions:
        if sub.parent_code is not None:
            continue
        result.append({
            "code": sub.code.split("-", 1)[-1],
            "iso_code": sub.code,
            "name": sub.name,
            "type": sub.type,
        })
    return sorted(result, key=lambda p: p["name"])


def get_provinces(country_iso2: str) -> list[dict]:
    return _provinces_cached(country_iso2.upper())


def get_province_by_code(country_iso2: str, code: str) -> Optional[dict]:
    code = code.upper()
    for p in get_provinces(country_iso2):
        if p["code"].upper() == code or p["iso_code"].upper() == code:
            return p
    return None


@lru_cache(maxsize=256)
def _cities_cached(country_iso2: str) -> list[dict]:
    cities = _gc.get_cities()
    result = [
        {
            "name": c["name"],
            "latitude": c.get("latitude"),
            "longitude": c.get("longitude"),
            "population": c.get("population", 0),
        }
        for c in cities.values()
        if c["countrycode"] == country_iso2
    ]
    return sorted(result, key=lambda c: (-c["population"], c["name"]))


def get_cities(country_iso2: str) -> list[dict]:
    return _cities_cached(country_iso2.upper())


def get_city_centroid(country_iso2: str, city_name: str) -> Optional[dict]:
    name_lower = city_name.lower().strip()
    for city in get_cities(country_iso2):
        if city["name"].lower() == name_lower:
            return {
                "name": city["name"],
                "latitude": city["latitude"],
                "longitude": city["longitude"],
            }
    return None


async def reverse_geocode(lat: float, lng: float, redis_client=None) -> Optional[dict]:
    cache_key = f"geo:reverse:{round(lat, 3)}:{round(lng, 3)}"

    if redis_client:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning("Redis cache read failed: %s", e)

    result = await _nominatim_reverse(lat, lng)
    if result is None:
        return None

    if redis_client:
        try:
            await redis_client.setex(cache_key, REVERSE_GC_CACHE_TTL, json.dumps(result))
        except Exception as e:
            logger.warning("Redis cache write failed: %s", e)

    return result


async def _nominatim_reverse(lat: float, lng: float) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={
                    "lat": lat,
                    "lon": lng,
                    "format": "json",
                    "addressdetails": 1,
                    "accept-language": "en",
                },
                headers={"User-Agent": NOMINATIM_USER_AGENT},
            )
            response.raise_for_status()
            data = response.json()

        address = data.get("address", {})
        return {
            "country": address.get("country"),
            "country_iso2": address.get("country_code", "").upper() or None,
            "province": (
                address.get("state")
                or address.get("province")
                or address.get("region")
                or address.get("county")
            ),
            "city": (
                address.get("city")
                or address.get("town")
                or address.get("municipality")
                or address.get("village")
                or address.get("hamlet")
            ),
        }

    except httpx.TimeoutException:
        logger.error("Nominatim timed out for (%s, %s)", lat, lng)
        return None
    except Exception as e:
        logger.error("Reverse geocoding failed for (%s, %s): %s", lat, lng, e)
        return None


def clear_cache() -> None:
    _countries_cached.cache_clear()
    _provinces_cached.cache_clear()
    _cities_cached.cache_clear()


# =============================================================================
# LocationService Class - For use in users.py
# =============================================================================

class LocationService:
    """Service class for location operations."""
    
    @staticmethod
    def validate_location(province: Optional[str] = None, city: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate that province and city exist in Iran.
        Returns: {"valid": bool, "error": Optional[str]}
        """
        # For now, just basic validation
        # Can be expanded to check against actual data
        if province is None and city is None:
            return {"valid": True, "error": None}
        
        # Basic validation - check if province/city are not empty
        if province is not None and len(province.strip()) == 0:
            return {"valid": False, "error": "Province cannot be empty"}
        
        if city is not None and len(city.strip()) == 0:
            return {"valid": False, "error": "City cannot be empty"}
        
        # Check if city exists in Iran (IR) dataset
        if city is not None:
            # Try to find city in Iran's cities
            cities = get_cities("IR")
            city_found = any(c["name"].lower() == city.lower() for c in cities)
            if not city_found:
                # Log warning but don't fail - user might be entering a city not in our dataset
                logger.warning(f"City '{city}' not found in Iran cities dataset")
                # Still allow it - cities dataset may not be complete
                pass
        
        return {"valid": True, "error": None}
    
    @staticmethod
    async def reverse_geocode(lat: float, lng: float) -> Optional[Dict[str, Any]]:
        """
        Reverse geocode coordinates to location text.
        Uses the global reverse_geocode function.
        """
        # Import redis client here to avoid circular imports
        from app.core.redis import redis_client
        result = await reverse_geocode(lat, lng, redis_client=redis_client)
        return result
    
    @staticmethod
    def get_countries() -> List[Dict[str, Any]]:
        """Get list of all countries."""
        return get_countries()
    
    @staticmethod
    def get_provinces(country_iso2: str) -> List[Dict[str, Any]]:
        """Get provinces for a country."""
        return get_provinces(country_iso2)
    
    @staticmethod
    def get_cities(country_iso2: str) -> List[Dict[str, Any]]:
        """Get cities for a country."""
        return get_cities(country_iso2)
    
    @staticmethod
    def get_city_centroid(country_iso2: str, city_name: str) -> Optional[Dict[str, Any]]:
        """Get centroid coordinates for a city."""
        return get_city_centroid(country_iso2, city_name)