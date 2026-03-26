# backend/config.py

from decouple import config


class Settings:
    SECRET_KEY: str = config("SECRET_KEY", default="change-me-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config(
        "ACCESS_TOKEN_EXPIRE_MINUTES", default=60, cast=int
    )
    DATABASE_URL: str = config("DATABASE_URL", default="sqlite:///./hiresmart.db")


settings = Settings()