from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    ML_API_BASE_URL: str = "https://api.mercadolibre.com"
    ML_ACCESS_TOKEN: str = ""
    ML_OFFLINE_MODE: bool = True
    ML_WEB_BASE_URL: str = "https://www.mercadolibre.com.ar"
    RATE_LIMIT_PER_HOUR: int = 1000
    REQUEST_DELAY_SECONDS: float = 0.1

    DATABASE_URL: str = "sqlite:///data/reviews.db"

    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    SENTIMENT_MODEL: str = "textblob"
    CACHE_EXPIRY_HOURS: int = 24

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

settings = Settings()
