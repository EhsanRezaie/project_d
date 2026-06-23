from typing import Optional
from pydantic import BaseModel


class CountryResponse(BaseModel):
    iso2: str
    iso3: str
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True


class ProvinceResponse(BaseModel):
    code: str
    iso_code: str
    name: str
    type: str

    class Config:
        from_attributes = True


class CityResponse(BaseModel):
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    population: Optional[int] = None

    class Config:
        from_attributes = True


class ReverseGeocodeResponse(BaseModel):
    country: Optional[str] = None
    country_iso2: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None