from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from typing import Optional

from app.core.limiter import limiter
from app.services.location_service import LocationService
from app.schemas.location import (
    ProvincesListResponse,
    ProvinceResponse,
    CitiesListResponse,
    CityResponse,
    LocationValidationResponse
)

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/provinces", response_model=ProvincesListResponse)
@limiter.limit("100/minute")
async def get_provinces(
    request: Request,
):
    """Get all Iranian provinces for frontend dropdown"""
    provinces = LocationService.get_provinces_list()
    return ProvincesListResponse(
        country="Iran",
        country_code="IR",
        provinces=[ProvinceResponse(**p) for p in provinces]
    )


@router.get("/cities", response_model=CitiesListResponse)
@limiter.limit("100/minute")
async def get_cities(
    request: Request,
    province_code: str = Query(..., description="Province code (e.g., 'THR' for Tehran)"),
):
    """Get cities for a specific province"""
    province = LocationService.get_province_by_code(province_code)
    if not province:
        raise HTTPException(
            status_code=404, 
            detail=f"Province with code '{province_code}' not found"
        )
    
    cities = LocationService.get_cities_list(province_code)
    return CitiesListResponse(
        province_code=province_code,
        cities=[CityResponse(**c) for c in cities]
    )


@router.get("/validate", response_model=LocationValidationResponse)
@limiter.limit("100/minute")
async def validate_location(
    request: Request,
    province: str = Query(..., description="Province name"),
    city: Optional[str] = Query(None, description="City name"),
):
    """Validate if province and city exist in Iran"""
    result = LocationService.validate_location(province, city)
    
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    province_obj = result["province_data"]
    city_obj = result["city_data"]
    
    return LocationValidationResponse(
        valid=True,
        province={
            "code": getattr(province_obj, "state_code", ""),
            "name": getattr(province_obj, "name", "")
        },
        city={
            "name": getattr(city_obj, "name", ""),
            "latitude": getattr(city_obj, "latitude", None),
            "longitude": getattr(city_obj, "longitude", None)
        } if city_obj else None
    )