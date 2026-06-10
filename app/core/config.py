from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "DatingApp"
    DEBUG: bool = False

    DATABASE_URL: str
    REDIS_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # Redis production settings
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_MAX_RETRIES: int = 3

    class Config:
        env_file = ".env"


settings = Settings()