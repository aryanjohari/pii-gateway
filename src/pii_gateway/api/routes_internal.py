"""Internal-only job triggers (protect with network policy + INTERNAL_JOB_API_KEY)."""

from fastapi import APIRouter, Request

from pii_gateway.api.auth import verify_internal_job
from pii_gateway.jobs.file_ingest import run_file_ingest_job
from pii_gateway.jobs.postgres_batch_job import run_postgres_batch_job

router = APIRouter(prefix="/internal/jobs", tags=["internal"])


@router.post("/postgres-batch")
async def trigger_postgres_batch(request: Request) -> dict[str, str | bool]:
    verify_internal_job(request, request.app.state.settings)
    await run_postgres_batch_job(request.app)
    return {"ok": True, "job": "postgres-batch"}


@router.post("/file-ingest")
async def trigger_file_ingest(request: Request) -> dict[str, str | bool]:
    verify_internal_job(request, request.app.state.settings)
    await run_file_ingest_job(request.app)
    return {"ok": True, "job": "file-ingest"}
