# app/schemas/location.py
from typing import Optional
from pydantic import BaseModel


class CountryResponse(BaseModel):
    iso2: str
    iso3: str
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone_code: Optional[str] = None
    currency: Optional[str] = None
    capital: Optional[str] = None
    region: Optional[str] = None
    subregion: Optional[str] = None
    native: Optional[str] = None
    tld: Optional[str] = None

    class Config:
        from_attributes = True


class ProvinceResponse(BaseModel):
    code: str
    iso_code: str
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country_code: Optional[str] = None
    type: Optional[str] = None

    class Config:
        from_attributes = True


class CityResponse(BaseModel):
    name: str
    province: Optional[str] = None  # This will be the state_code
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