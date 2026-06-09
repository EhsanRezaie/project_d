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

    class Config:
        env_file = ".env"


settings = Settings()
