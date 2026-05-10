from __future__ import annotations
import json
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DAILY_FINE_RATE: float = 500.0
    TAX_RATE: float = 0.18
    # Plain string — avoids pydantic-settings JSON-decoding the value before
    # we get a chance to parse it.  Accepts any of:
    #   *
    #   https://app.onrender.com,http://localhost:5173
    #   ["https://app.onrender.com"]
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        v = self.ALLOWED_ORIGINS.strip()
        if v.startswith("["):
            return json.loads(v)
        return [o.strip() for o in v.split(",") if o.strip()]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
