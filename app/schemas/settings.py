from typing import Optional
from pydantic import BaseModel
from uuid import UUID


class UserSettingsResponse(BaseModel):
    hide_last_seen: bool = False
    hide_online_status: bool = False
    push_enabled: bool = True
    like_notifications: bool = True
    match_notifications: bool = True
    message_notifications: bool = True
    language: str = "fa"
    dark_mode: bool = False

    class Config:
        from_attributes = True


class UserSettingsUpdateRequest(BaseModel):
    hide_last_seen: Optional[bool] = None
    hide_online_status: Optional[bool] = None
    push_enabled: Optional[bool] = None
    like_notifications: Optional[bool] = None
    match_notifications: Optional[bool] = None
    message_notifications: Optional[bool] = None
    language: Optional[str] = None
    dark_mode: Optional[bool] = None