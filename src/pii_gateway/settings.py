"""12-factor settings from environment (no secrets in repo)."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    pii_gateway_config_path: Path | None = Field(default=None)
    sanitize_http_api_key: str | None = Field(default=None)

    cors_allowed_origins: str = Field(default="")

    storage_backend: Literal["local", "s3"] = Field(default="local")
    storage_local_path: Path = Field(default=Path("/data/out"))

    s3_endpoint_url: str | None = Field(default=None)
    s3_bucket: str | None = Field(default=None)
    s3_prefix: str = Field(default="")
    aws_access_key_id: str | None = Field(default=None)
    aws_secret_access_key: str | None = Field(default=None)
    aws_region: str = Field(default="us-east-1")

    inbox_s3_bucket: str | None = Field(default=None)
    inbox_s3_prefix: str = Field(default="")

    postgres_batch_dsn: str | None = Field(default=None)
    postgres_batch_cron: str | None = Field(default=None)
    batch_file_poll_seconds: int | None = Field(default=None)

    internal_job_api_key: str | None = Field(default=None)

    batch_demo_fixture: bool = Field(default=False)
    batch_csv_max_bytes: int = Field(default=52428800)
    gateway_state_dir: Path = Field(default=Path("/data/state"))
    disable_scheduler: bool = Field(default=False)


def load_settings() -> Settings:
    return Settings()
