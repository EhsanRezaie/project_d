from pydantic import BaseModel


class SwipeStatsResponse(BaseModel):
    """Response schema for swipe statistics."""
    daily_likes_remaining: int
    is_unlimited: bool
    total_likes_sent: int
    total_passes_sent: int
    total_matches: int
    ads_watched_today: int
    max_ads_per_day: int