from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_path: str = "chan_osint.db"
    image_dir: str = "data/images"
    request_delay: float = 1.1
    archive_delay: float = 2.0
    pivot_delay: float = 2.0
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    github_token: str = ""
    hibp_api_key: str = ""
    nominatim_email: str = ""


settings = Settings()
