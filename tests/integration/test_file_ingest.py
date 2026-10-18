"""Local inbox ingest: happy paths, bad file, and idempotence."""

import json
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi import FastAPI

from pii_gateway.jobs.file_ingest import run_file_ingest_job


def _cleaned_artifacts(app_root: Path) -> list[Path]:
    return sorted((app_root / "out" / "cleaned").rglob("*.jsonl"))


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("users.csv", "email,note\nalice@example.com,hello\nbob@example.com,hi\n"),
        (
            "users.json",
            json.dumps(
                [
                    {"email": "alice@example.com", "note": "hello"},
                    {"email": "bob@example.com", "note": "hi"},
                ]
            ),
        ),
    ],
)
async def test_inbox_file_is_redacted_into_one_artifact(
    tmp_path: Path, make_job_app: Callable[..., FastAPI], filename: str, content: str
) -> None:
    app = make_job_app()
    (tmp_path / "inbox" / filename).write_text(content, encoding="utf-8")

    await run_file_ingest_job(app)

    artifacts = _cleaned_artifacts(tmp_path)
    assert len(artifacts) == 1
    lines = artifacts[0].read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert "example.com" not in "".join(lines)
    assert json.loads(lines[0])["email"] == "<EMAIL_ADDRESS>"


async def test_bad_file_is_skipped_without_blocking_good_files(
    tmp_path: Path, make_job_app: Callable[..., FastAPI]
) -> None:
    app = make_job_app()
    inbox = tmp_path / "inbox"
    (inbox / "a_broken.json").write_text("{not json", encoding="utf-8")
    (inbox / "b_good.csv").write_text("email,note\nalice@example.com,hi\n", encoding="utf-8")

    await run_file_ingest_job(app)

    assert len(_cleaned_artifacts(tmp_path)) == 1
    processed = json.loads((tmp_path / "state" / "processed_files.json").read_text())
    assert [Path(key).name for key in processed] == ["b_good.csv"]


async def test_unchanged_file_is_not_processed_twice(
    tmp_path: Path, make_job_app: Callable[..., FastAPI]
) -> None:
    app = make_job_app()
    (tmp_path / "inbox" / "users.csv").write_text(
        "email,note\nalice@example.com,hi\n", encoding="utf-8"
    )

    await run_file_ingest_job(app)
    await run_file_ingest_job(app)

    assert len(_cleaned_artifacts(tmp_path)) == 1
