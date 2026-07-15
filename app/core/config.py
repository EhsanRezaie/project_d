# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ============================================
    # App Settings
    # ============================================
    APP_NAME: str = "Bondi"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    TESTING: bool = False

    # ============================================
    # Database & Redis
    # ============================================
    DATABASE_URL: str
    REDIS_URL: str

    # ============================================
    # Security
    # ============================================
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # ============================================
    # Google OAuth
    # ============================================
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # ============================================
    # Admin
    # ============================================
    ADMIN_SECRET_KEY: str = ""
    ADMIN_USERNAME: str = ""
    ADMIN_PASSWORD_HASH: str = ""

    # ============================================
    # Redis Settings
    # ============================================
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_MAX_RETRIES: int = 3

    # ============================================
    # Daily Limits & Rewards
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

    # ============================================
    # Payment
    # ============================================
    ZARINPAL_MERCHANT_ID: str = ""
    ZARINPAL_SANDBOX: bool = True
    ZARINPAL_CALLBACK_URL: str = ""

    # ============================================
    # File Uploads
    # ============================================
    MAX_PHOTO_SIZE_MB: int = 10
    MAX_PHOTOS_PER_USER: int = 9
    
    # ============================================
    # Chat Media Settings
    # ============================================
    MAX_CHAT_PHOTO_SIZE_MB: int = 5
    MAX_CHAT_VOICE_SIZE_MB: int = 2
    MAX_CHAT_VOICE_DURATION: int = 120
    ALLOWED_CHAT_IMAGE_FORMATS: str
    
    # ============================================
    # MinIO / S3 Settings (NO DEFAULTS - MUST BE IN .env)
    # ============================================
    S3_ENDPOINT_URL: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_REGION: str
    S3_PUBLIC_BUCKET: str
    S3_PRIVATE_BUCKET: str
    S3_PUBLIC_BASE_URL: str
    S3_SIGNED_URL_EXPIRE_SECONDS: int
    
    # ===========================================
    # Encryption
    # ===========================================
    ENCRYPTION_SECRET: str
    
    # ============================================
    # App Version
    # ============================================
    APP_VERSION: str
    MIN_ANDROID_VERSION: str
    MIN_IOS_VERSION: str
    
    # ============================================
    # App Store Links
    # ============================================
    PLAY_STORE_URL: str
    APP_STORE_URL: str
    
    # ============================================
    # Force Update
    # ============================================
    FORCE_UPDATE_ENABLED: bool
    FORCE_UPDATE_MESSAGE: str

    # ============================================
    # Error Tracking (GlitchTip)
    # ============================================
    GLITCHTIP_DSN: str = ""

    # ============================================
    # FCM Push Notifications
    # ============================================
    FCM_SERVICE_ACCOUNT_PATH: str = ""

    # ============================================
    # NSFW Detection
    # ============================================
    NSFW_ENABLED: bool = True
    NSFW_THRESHOLD: float = 0.8

    # ============================================
    # CORS
    # ============================================
    CORS_ORIGINS: str = ""

    # ============================================
    # Pydantic Config
    # ============================================
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


settings = Settings()