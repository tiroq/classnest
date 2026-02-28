"""Application configuration loaded from environment variables."""

import functools
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for ClassNest loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    bot_token: str = Field(..., alias="BOT_TOKEN")

    # Database
    db_sqlite_path: str = Field("data/classnest.db", alias="DB_SQLITE_PATH")

    # File paths
    cache_dir: str = Field("data/cache", alias="CACHE_DIR")
    export_dir: str = Field("data/exports", alias="EXPORT_DIR")

    # Admin panel
    admin_host: str = Field("0.0.0.0", alias="ADMIN_HOST")
    admin_port: int = Field(8000, alias="ADMIN_PORT")
    admin_username: str = Field("admin", alias="ADMIN_USERNAME")
    admin_password: str = Field("changeme", alias="ADMIN_PASSWORD")

    def ensure_dirs(self) -> None:
        """Create required directories if they do not exist."""
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        Path(self.export_dir).mkdir(parents=True, exist_ok=True)
        Path(self.db_sqlite_path).parent.mkdir(parents=True, exist_ok=True)


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance (thread-safe via lru_cache)."""
    return Settings()
