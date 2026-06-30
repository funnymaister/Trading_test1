from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BingX Shortlist API"
    app_env: str = "dev"
    app_debug: bool = True

    host: str = "127.0.0.1"
    port: int = 8000

    bingx_base_url: str = "https://open-api.bingx.com"
    bingx_symbols_path: str = "/openApi/swap/v2/quote/contracts"

    cache_ttl_seconds: int = 60
    http_timeout_seconds: float = 20.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def debug(self) -> bool:
        return self.app_debug


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()