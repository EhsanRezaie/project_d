import httpx
from functools import lru_cache
from typing import Optional, Dict, List, Any
from countrystatecity_countries import get_country_by_code, get_states_of_country, get_cities_of_state


class LocationService:
    """Service for handling location data (countries, states/provinces, cities)"""
    
    @staticmethod
    def get_iran_country() -> Optional[Any]:
        """Get Iran country data"""
        return get_country_by_code("IR")
    
    @staticmethod
    def get_all_provinces() -> List[Any]:
        """Get all Iranian provinces (states)"""
        states = get_states_of_country("IR")
        return states or []
    
    @staticmethod
    def get_cities_by_province(province_code: str) -> List[Any]:
        """Get all cities in a specific province"""
        cities = get_cities_of_state("IR", province_code)
        return cities or []
    
    @staticmethod
    def get_province_by_name(province_name: str) -> Optional[Any]:
        """Find province by name (case-insensitive)"""
        provinces = LocationService.get_all_provinces()
        for province in provinces:
            province_name_attr = getattr(province, "name", "")
            province_code_attr = getattr(province, "state_code", "")
            if province_name_attr.lower() == province_name.lower():
                return province
            if province_code_attr.lower() == province_name.lower():
                return province
        return None
    
    @staticmethod
    def get_province_by_code(province_code: str) -> Optional[Any]:
        """Find province by code"""
        provinces = LocationService.get_all_provinces()
        for province in provinces:
            code = getattr(province, "state_code", "")
            if code.lower() == province_code.lower():
                return province
        return None
    
    @staticmethod
    def get_city_by_name(province_code: str, city_name: str) -> Optional[Any]:
        """Find city by name in a specific province"""
        cities = LocationService.get_cities_by_province(province_code)
        for city in cities:
            city_name_attr = getattr(city, "name", "")
            if city_name_attr.lower() == city_name.lower():
                return city
        return None
    
    @staticmethod
    def validate_location(province: str, city: str = None) -> Dict:
        """
        Validate province and optional city exist in Iran
        Returns: {"valid": bool, "province_data": dict, "city_data": dict, "error": str}
        """
        province_data = LocationService.get_province_by_name(province)
        if not province_data:
            return {
                "valid": False,
                "province_data": None,
                "city_data": None,
                "error": f"Province '{province}' not found in Iran"
            }
        
        city_data = None
        if city:
            province_code = getattr(province_data, "state_code", "")
            city_data = LocationService.get_city_by_name(province_code, city)
            if not city_data:
                return {
                    "valid": False,
                    "province_data": province_data,
                    "city_data": None,
                    "error": f"City '{city}' not found in province '{province}'"
                }
        
        return {
            "valid": True,
            "province_data": province_data,
            "city_data": city_data,
            "error": None
        }
    
    @staticmethod
    @lru_cache(maxsize=1)
    def get_provinces_list_cached() -> List[Dict]:
        """Cached version of provinces list - provinces rarely change"""
        provinces = LocationService.get_all_provinces()
        return [
            {
                "code": getattr(p, "state_code", ""),
                "name": getattr(p, "name", ""),
                "country_code": getattr(p, "country_code", "")
            }
            for p in provinces
        ]
    
    @staticmethod
    def get_provinces_list() -> List[Dict]:
        """Get simplified list of provinces for frontend dropdown"""
        return LocationService.get_provinces_list_cached()
    
    @staticmethod
    @lru_cache(maxsize=32)
    def get_cities_list_cached(province_code: str) -> List[Dict]:
        """Cached version of cities list for a province"""
        cities = LocationService.get_cities_by_province(province_code)
        return [
            {
                "name": getattr(c, "name", ""),
                "latitude": getattr(c, "latitude", None),
                "longitude": getattr(c, "longitude", None)
            }
            for c in cities
        ]
    
    @staticmethod
    def get_cities_list(province_code: str) -> List[Dict]:
        """Get simplified list of cities for frontend dropdown"""
        return LocationService.get_cities_list_cached(province_code)
    
    @staticmethod
    async def reverse_geocode(lat: float, lng: float) -> Optional[Dict]:
        """Get province/city from coordinates using Nominatim (OpenStreetMap)"""
        try:
            async with httpx.AsyncClient() as client:
                url = "https://nominatim.openstreetmap.org/reverse"
                params = {
                    "lat": lat,
                    "lon": lng,
                    "format": "json",
                    "addressdetails": 1,
                    "accept-language": "en"
                }
                response = await client.get(url, params=params, timeout=10.0)
                data = response.json()
                
                address = data.get("address", {})
                
                country = address.get("country")
                province = address.get("state") or address.get("province")
                city = address.get("city") or address.get("town") or address.get("village")
                
                return {
                    "country": country,
                    "province": province,
                    "city": city
                }
        except Exception as e:
            from app.core.logging import get_logger
            logger = get_logger("location_service")
            logger.error(f"Reverse geocoding failed for ({lat}, {lng}): {e}")
            return None
    
    @staticmethod
    def clear_cache():
        """Clear all cached location data (useful for testing)"""
        LocationService.get_provinces_list_cached.cache_clear()
        LocationService.get_cities_list_cached.cache_clear()