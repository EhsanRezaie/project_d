# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "DatingApp"
    DEBUG: bool = False

    DATABASE_URL: str
    REDIS_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    ADMIN_SECRET_KEY: str = ""

    # Redis settings
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_MAX_RETRIES: int = 3

    # ============================================
    # SESSION 11: Daily Limits & Rewards
    # NO DEFAULTS HERE - must be in .env
    # ============================================
    
    FREE_USER_DAILY_LIKES: int
    FREE_USER_DAILY_CHATS: int
    
    AD_REWARD_LIKES_BONUS: int
    AD_REWARD_CHATS_BONUS: int
    
    MAX_AD_REWARDS_PER_DAY: int
    
    WELCOME_BONUS_DAYS: int
    
    REFERRAL_INVITER_DAYS: int
    REFERRAL_INVITED_DAYS: int
    
    SUBSCRIPTION_MONTHLY_DAYS: int
    SUBSCRIPTION_QUARTERLY_DAYS: int
    SUBSCRIPTION_YEARLY_DAYS: int
    
    SUBSCRIPTION_QUARTERLY_DISCOUNT: int
    SUBSCRIPTION_YEARLY_DISCOUNT: int
    
    ZARINPAL_MERCHANT_ID: str = ""
    ZARINPAL_SANDBOX: bool = True
    ZARINPAL_CALLBACK_URL: str = ""
    
    UPLOADS_DIR: str = "uploads"
    MAX_PHOTO_SIZE_MB: int = 5
    MAX_PHOTOS_PER_USER: int = 6

    class Config:
        env_file = ".env"


settings = Settings()