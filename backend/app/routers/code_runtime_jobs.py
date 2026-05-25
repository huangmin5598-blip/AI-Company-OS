# @PRODUCT Router — v0.9.1.1 Code Runtime Jobs
"""Endpoints for async code runtime job lifecycle.

Code Runtime Jobs decouple the HTTP request lifecycle from long-running
Codex CLI subprocess calls (40-90s). Instead of blocking until Codex finishes,
we create a job (status=queued), return immediately, and the caller polls
GET /code-runtime-jobs/{id} for the result.

Flow:
  POST   /code-runtime-jobs                    → create + start job → return { job_id }
  GET    /code-runtime-jobs                    → list recent jobs
  GET    /code-runtime-jobs/{id}               → poll job status + result
  POST   /code-runtime-jobs/{id}/retry         → retry a failed job
"""

import json
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import get_sync_session
from app.models.code_runtime_job import CodeRuntimeJob

router = APIRouter(prefix="/api/v1/code-runtime-jobs", tags=["code_runtime"])

# ── Pydantic schemas ──


class CreateJobRequest(BaseModel):
    request_type: str  # plan / patch / checks
    source_type: str = "code_change_request"
    source_id: int | None = None
    runtime_id: str = "codex"
    prompt: str | None = None


class RetryJobRequest(BaseModel):
    pass


# ── Serializer ──


def _serialize(job: CodeRuntimeJob) -> dict:
    return {
        "id": job.id,
        "request_type": job.request_type,
        "source_type": job.source_type,
        "source_id": job.source_id,
        "runtime_id": job.runtime_id,
        "status": job.status,
        "run_id": job.run_id,
        "run_stdout_path": job.run_stdout_path,
        "run_stderr_path": job.run_stderr_path,
        "result_text": job.result_text,
        "error_text": job.error_text,
        "elapsed_seconds": job.elapsed_seconds,
        "exit_code": job.exit_code,
        "started_at": str(job.started_at) if job.started_at else None,
        "finished_at": str(job.finished_at) if job.finished_at else None,
        "created_at": str(job.created_at) if job.created_at else None,
        "updated_at": str(job.updated_at) if job.updated_at else None,
    }


# ── Endpoints ──


@router.get("")
def list_jobs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str = Query(None, description="Filter by status"),
):
    session = get_sync_session()
    try:
        q = session.query(CodeRuntimeJob).order_by(CodeRuntimeJob.id.desc())
        if status:
            q = q.filter(CodeRuntimeJob.status == status)
        return [_serialize(j) for j in q.offset(offset).limit(limit).all()]
    finally:
        session.close()


@router.get("/{job_id}")
def get_job(job_id: int):
    session = get_sync_session()
    try:
        job = session.query(CodeRuntimeJob).filter_by(id=job_id).first()
        if not job:
            raise HTTPException(404, "Code runtime job not found")
        return _serialize(job)
    finally:
        session.close()


@router.post("")
async def create_job(req: CreateJobRequest):
    """Create a new code runtime job and queue it for execution.

    Returns immediately with job_id and status='queued'.
    Codex runs in a background thread; use GET /{job_id} to poll.
    """
    import asyncio
    import threading

    session = get_sync_session()
    try:
        job = CodeRuntimeJob(
            request_type=req.request_type,
            source_type=req.source_type,
            source_id=req.source_id,
            runtime_id=req.runtime_id,
            status="queued",
        )
        session.add(job)
        session.commit()
        job_id = job.id
        session.close()

        repo_root = os.path.expanduser("~/Documents/Codex/ai-company-os")
        prompt = req.prompt or "Read relevant files and generate a plan."
        runtime_type = req.runtime_id or "codex"

        def _execute_job_sync():
            """Sync function that runs in a background thread.
            Creates its own event loop for the async Codex call.
            """
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_run_job(
                    job_id=job_id,
                    prompt=prompt,
                    runtime_type=runtime_type,
                    repo_root=repo_root,
                ))
            finally:
                loop.close()

        thread = threading.Thread(target=_execute_job_sync, daemon=True)
        thread.start()

        return {"job_id": job_id, "status": "queued", "message": "Job created and queued for execution"}

    except Exception as e:
        try:
            session.rollback()
        except Exception:
            pass
        raise HTTPException(500, f"Failed to create job: {str(e)[:200]}")
    finally:
        try:
            session.close()
        except Exception:
            pass


async def _run_job(job_id: int, prompt: str, runtime_type: str, repo_root: str):
    """Async job execution — runs Codex and updates DB."""
    from app.code_bridge.planner import CodePlanner

    db_session = get_sync_session()
    try:
        db_job = db_session.query(CodeRuntimeJob).filter_by(id=job_id).first()
        if not db_job:
            return
        db_job.status = "running"
        db_job.started_at = datetime.utcnow()
        db_session.commit()

        planner = CodePlanner(runtime_type=runtime_type)
        result = await planner.generate(
            problem=prompt,
            workdir=repo_root,
        )

        db_job.status = "success"
        db_job.result_text = result.plan_summary
        db_job.finished_at = datetime.utcnow()
        if result.elapsed_seconds:
            db_job.elapsed_seconds = int(result.elapsed_seconds)
        db_session.commit()

    except Exception as e:
        try:
            db_job = db_session.query(CodeRuntimeJob).filter_by(id=job_id).first()
            if db_job:
                db_job.status = "failed"
                db_job.error_text = str(e)[:2000]
                db_job.finished_at = datetime.utcnow()
                db_session.commit()
        except Exception:
            pass
    finally:
        db_session.close()


@router.post("/{job_id}/retry")
def retry_job(job_id: int, req: RetryJobRequest = RetryJobRequest()):
    """Reset a failed job back to queued for retry."""
    session = get_sync_session()
    try:
        job = session.query(CodeRuntimeJob).filter_by(id=job_id).first()
        if not job:
            raise HTTPException(404, "Code runtime job not found")
        if job.status not in ("failed", "timeout"):
            raise HTTPException(400, f"Cannot retry job in status '{job.status}'")

        job.status = "queued"
        job.error_text = None
        job.result_text = None
        job.started_at = None
        job.finished_at = None
        job.exit_code = None
        job.elapsed_seconds = None
        job.run_id = None
        session.commit()

        return {"job_id": job.id, "status": "queued", "message": "Job reset for retry"}
    finally:
        session.close()
