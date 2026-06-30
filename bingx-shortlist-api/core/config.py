from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BingX Shortlist API"
    app_env: str = "dev"

    bingx_base_url: str = "https://open-api.bingx.com"
    bingx_api_key: str = ""
    bingx_api_secret: str = ""
    bingx_source_key: str = ""

    bingx_recv_window: int = 5000
    bingx_timeout_seconds: int = 15
    enable_live_bingx: bool = False

    scanner_enabled: bool = True
    scanner_interval_seconds: int = 30
    scanner_top_movers_limit: int = 20

    internal_api_key: str = "dev-internal-key"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    scanner_enabled: bool = True
    scanner_interval_seconds: int = 30
    scanner_top_movers_limit: int = 20
    return Settings()