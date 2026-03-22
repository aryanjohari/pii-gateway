"""Local JSON state (cursors, processed file index). Never store raw PII."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def read_json_file(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_file(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def postgres_cursor_path(state_dir: Path) -> Path:
    return state_dir / "postgres_batch_cursor.json"


def load_postgres_since(state_dir: Path) -> datetime:
    raw = read_json_file(postgres_cursor_path(state_dir), {})
    ts = raw.get("last_run") if isinstance(raw, dict) else None
    if not ts or not isinstance(ts, str):
        return datetime(1970, 1, 1, tzinfo=UTC)
    return datetime.fromisoformat(ts)


def save_postgres_cursor(state_dir: Path, when: datetime) -> None:
    write_json_file(postgres_cursor_path(state_dir), {"last_run": when.isoformat()})


def processed_files_path(state_dir: Path) -> Path:
    return state_dir / "processed_files.json"


def load_processed_index(state_dir: Path) -> dict[str, dict[str, int | str]]:
    raw = read_json_file(processed_files_path(state_dir), {})
    if isinstance(raw, dict):
        out: dict[str, dict[str, int | str]] = {}
        for k, v in raw.items():
            if isinstance(v, dict):
                out[str(k)] = {str(kk): vv for kk, vv in v.items()}
        return out
    return {}


def save_processed_index(state_dir: Path, data: dict[str, dict[str, int | str]]) -> None:
    write_json_file(processed_files_path(state_dir), data)


def fingerprint_local_file(path: Path) -> dict[str, int | str]:
    st = path.stat()
    return {"mtime_ns": int(st.st_mtime_ns), "size": int(st.st_size)}
