from typing import Optional
from pydantic import BaseModel


class PrivacySettingsResponse(BaseModel):
    hide_last_seen: bool = False  


class PrivacySettingsUpdate(BaseModel):
    hide_last_seen: Optional[bool] = None