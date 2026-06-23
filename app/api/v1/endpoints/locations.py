from fastapi import APIRouter, HTTPException, Query, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.limiter import limiter
from app.db.session import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.models.user_profile import UserProfile
from app.services.location_service import (
    get_countries,
    get_country_by_iso2,
    get_provinces,
    get_province_by_code,
    get_cities,
    get_city_centroid,
    reverse_geocode,
)
from app.schemas.location import (
    CountryResponse,
    ProvinceResponse,
    CityResponse,
    ReverseGeocodeResponse,
)

router = APIRouter(prefix="/locations", tags=["locations"])


# ---------------------------------------------------------------------------
# Public reference endpoints (no auth — needed during onboarding before JWT)
# ---------------------------------------------------------------------------

@router.get("/countries", response_model=list[CountryResponse])
@limiter.limit("60/minute")
async def list_countries(request: Request):
    """All countries sorted alphabetically. Used to populate the country picker."""
    return get_countries()


@router.get("/provinces", response_model=list[ProvinceResponse])
@limiter.limit("60/minute")
async def list_provinces(
    request: Request,
    country: str = Query(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code (e.g. 'IR', 'US')"),
):
    """
    Provinces / states / regions for a country (ISO 3166-2, top-level only).
    Returns empty list for countries with no subdivision data.
    """
    country = country.upper()
    if not get_country_by_iso2(country):
        raise HTTPException(status_code=404, detail=f"Country '{country}' not found")
    return get_provinces(country)


@router.get("/cities", response_model=list[CityResponse])
@limiter.limit("60/minute")
async def list_cities(
    request: Request,
    country: str = Query(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code"),
):
    """
    Cities for a country, sorted by population descending.
    Flutter shows this as a searchable field — no server-side province
    filtering since GeoNames admin1codes don't align with ISO subdivision
    codes for most non-US countries.
    """
    country = country.upper()
    if not get_country_by_iso2(country):
        raise HTTPException(status_code=404, detail=f"Country '{country}' not found")
    return get_cities(country)


@router.get("/reverse-geocode", response_model=ReverseGeocodeResponse)
@limiter.limit("30/minute")
async def reverse_geocode_endpoint(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
):
    """
    Convert GPS coordinates to country / province / city names.
    Used when user grants location permission. Results cached in Redis for 24h.
    Returns partial results (some fields null) if Nominatim can't resolve fully.
    """
    from app.core.redis import redis_client
    result = await reverse_geocode(lat, lng, redis_client=redis_client)
    if result is None:
        raise HTTPException(
            status_code=503,
            detail="Reverse geocoding service unavailable. Please enter location manually.",
        )
    return ReverseGeocodeResponse(**result)


@router.get("/city-centroid", response_model=CityResponse)
@limiter.limit("60/minute")
async def city_centroid(
    request: Request,
    country: str = Query(..., min_length=2, max_length=2),
    city: str = Query(..., min_length=1, max_length=100),
):
    """
    Estimate lat/lng for a manually selected city.
    Used when user does NOT grant GPS permission — stores approximate
    coordinates so the discovery/matching engine can still calculate distances.
    Sets location_manual=True on the user profile.
    """
    country = country.upper()
    centroid = get_city_centroid(country, city)
    if centroid is None:
        raise HTTPException(
            status_code=404,
            detail=f"City '{city}' not found in country '{country}'",
        )
    return CityResponse(**centroid)


# ---------------------------------------------------------------------------
# Authenticated: update user location
# ---------------------------------------------------------------------------

@router.patch("/me/location-gps")
@limiter.limit("10/minute")
async def update_location_gps(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Update user location from GPS coordinates.
    Reverse-geocodes to fill country/province/city text fields.
    Sets location_manual=False.
    """
    from sqlalchemy import select
    from app.core.redis import redis_client

    result = await reverse_geocode(lat, lng, redis_client=redis_client)

    profile_result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile.lat = lat
    profile.lng = lng
    profile.location_manual = False

    if result:
        profile.country = result.get("country")
        profile.province = result.get("province")
        profile.city = result.get("city")

    await session.commit()
    await session.refresh(profile)

    return {
        "lat": profile.lat,
        "lng": profile.lng,
        "country": profile.country,
        "province": profile.province,
        "city": profile.city,
        "location_manual": profile.location_manual,
    }


@router.patch("/me/location-manual")
@limiter.limit("10/minute")
async def update_location_manual(
    request: Request,
    country: str = Query(..., min_length=2, max_length=100),
    province: str = Query(..., min_length=1, max_length=100),
    city: str = Query(..., min_length=1, max_length=100),
    country_iso2: str = Query(..., min_length=2, max_length=2),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Update user location from manual country/province/city selection.
    Estimates lat/lng from city centroid. Sets location_manual=True.
    """
    from sqlalchemy import select

    profile_result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile.country = country
    profile.province = province
    profile.city = city
    profile.location_manual = True

    # Best-effort centroid estimation — fine to be null if city not in our dataset
    centroid = get_city_centroid(country_iso2.upper(), city)
    if centroid:
        profile.lat = centroid["latitude"]
        profile.lng = centroid["longitude"]

    await session.commit()
    await session.refresh(profile)

    return {
        "lat": profile.lat,
        "lng": profile.lng,
        "country": profile.country,
        "province": profile.province,
        "city": profile.city,
        "location_manual": profile.location_manual,
    }