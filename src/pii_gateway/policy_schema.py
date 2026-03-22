"""Mounted policy file schema (non-secret)."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class BatchQueryDef(BaseModel):
    sql: str
    params_from: Literal["last_run_cursor", "none"] | None = None


class PostgresBatchConfig(BaseModel):
    enabled: bool = False
    query_name: str = ""
    queries: dict[str, BatchQueryDef] = Field(default_factory=dict)


class BatchFileIngestConfig(BaseModel):
    mode: Literal["local", "s3"] = "local"
    local_path: Path = Field(default=Path("/data/inbox"))
    poll_seconds: int = 60
    s3_bucket: str = ""
    s3_prefix: str = ""


class PersistenceConfig(BaseModel):
    write_raw: bool = False
    write_cleaned: bool = True


class GatewayPolicy(BaseModel):
    config_version: int = 1
    redaction_entities: list[str] = Field(default_factory=list)
    structured_field_rules: dict[str, Literal["redact", "tokenize", "mask", "passthrough"]] = Field(
        default_factory=dict
    )
    postgres_batch: PostgresBatchConfig = Field(default_factory=PostgresBatchConfig)
    batch_file_ingest: BatchFileIngestConfig = Field(default_factory=BatchFileIngestConfig)
    persistence: PersistenceConfig = Field(default_factory=PersistenceConfig)
