from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DAILY_FINE_RATE: float = 500.0
    TAX_RATE: float = 0.18
    # Accepts JSON array OR comma-separated string, e.g.:
    #   ALLOWED_ORIGINS=https://app.onrender.com,http://localhost:5173
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
