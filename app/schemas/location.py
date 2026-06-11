from typing import Optional, List
from pydantic import BaseModel


class ProvinceResponse(BaseModel):
    """Province data for frontend dropdown"""
    code: str
    name: str
    country_code: str


class ProvincesListResponse(BaseModel):
    """Response for GET /locations/provinces"""
    country: str
    country_code: str
    provinces: List[ProvinceResponse]


class CityResponse(BaseModel):
    """City data for frontend dropdown"""
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CitiesListResponse(BaseModel):
    """Response for GET /locations/cities"""
    province_code: str
    cities: List[CityResponse]


class LocationValidationResponse(BaseModel):
    """Response for GET /locations/validate"""
    valid: bool
    province: Optional[dict] = None
    city: Optional[dict] = None


class LocationTextUpdateResponse(BaseModel):
    """Response for PATCH /users/me/location-text"""
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    location_manual: bool