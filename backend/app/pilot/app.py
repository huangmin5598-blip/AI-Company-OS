"""Independent loopback-only FastAPI surface for the VS-001 pilot."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.pilot.bootstrap import bootstrap_pilot_database
from app.pilot.database import (
    PILOT_AUTHORITY,
    PILOT_DB_PATH,
    PilotBoundaryViolation,
    PilotDatabase,
    operational_hash_status,
)
from app.pilot.demo_spine import DemoSpineStore
from app.pilot.gateway import PILOT_MODE, PilotCommandGateway
from app.pilot.real_workbench import RealWorkbenchStore


database = PilotDatabase()
gateway = PilotCommandGateway(database)
demo_spine_store = DemoSpineStore()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    bootstrap_pilot_database(database)
    yield
    database.dispose()


app = FastAPI(
    title="AI Company OS VS-001 Local Pilot",
    version="0.47-vs001",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Idempotency-Key"],
)


class CreateDraftBody(BaseModel):
    skill_id: str = Field(min_length=1, max_length=160)
    task_type: str = Field(min_length=1, max_length=160)
    input_context: str = Field(min_length=1, max_length=65536)
    expected_output: str = Field(min_length=1, max_length=4096)


class ExecuteBody(BaseModel):
    heading: str = Field(min_length=1, max_length=200)
    body: str = Field(max_length=65536)


class ReviewBody(BaseModel):
    decision: str = "passed"


class CreateDemoRunBody(BaseModel):
    offer_id: str = Field(min_length=1, max_length=120)
    founder_goal: str = Field(min_length=1, max_length=4096)


class CreateRealWorkbenchRunBody(BaseModel):
    product_line_id: str = Field(min_length=1, max_length=120)
    founder_goal: str = Field(min_length=1, max_length=4096)


class DemoDecisionBody(BaseModel):
    decision: str = Field(pattern="^(go|no_go)$")


def _context(
    request: Request,
    idempotency_key: str,
):
    host = request.client.host if request.client is not None else ""
    return gateway.founder_request(
        client_host=host,
        forwarded_for=request.headers.get("x-forwarded-for"),
        idempotency_key=idempotency_key,
    )


def _translate_error(exc: Exception) -> HTTPException:
    if isinstance(exc, LookupError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, (PermissionError, PilotBoundaryViolation)):
        return HTTPException(status_code=403, detail=str(exc))
    return HTTPException(status_code=409, detail=str(exc))


@app.get("/api/v1/vs001/status")
def status():
    return {
        "mode": PILOT_MODE,
        "authority": PILOT_AUTHORITY,
        "database_path": str(PILOT_DB_PATH),
        "banner": (
            "Local Pilot / OS-Governed / Non-production / "
            "Not Operational Authority"
        ),
        "operational_database": operational_hash_status(),
    }


@app.get("/api/v1/vs001/work-orders")
def list_work_orders(request: Request):
    try:
        context = _context(request, "read:list")
        return {"work_orders": gateway.list_work_orders(context)}
    except Exception as exc:
        raise _translate_error(exc) from exc


@app.get("/api/v1/vs001/work-orders/{work_order_id}")
def get_work_order(work_order_id: str, request: Request):
    try:
        context = _context(request, f"read:{work_order_id}")
        return gateway.get_work_order(context, work_order_id)
    except Exception as exc:
        raise _translate_error(exc) from exc


@app.post("/api/v1/vs001/work-orders")
def create_work_order(
    body: CreateDraftBody,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
):
    try:
        return gateway.create_draft(
            _context(request, idempotency_key),
            **body.model_dump(),
        )
    except Exception as exc:
        raise _translate_error(exc) from exc


@app.post("/api/v1/vs001/work-orders/{work_order_id}/request-approval")
def request_approval(
    work_order_id: str,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
):
    try:
        return gateway.request_approval(
            _context(request, idempotency_key),
            work_order_id,
        )
    except Exception as exc:
        raise _translate_error(exc) from exc


@app.post("/api/v1/vs001/work-orders/{work_order_id}/approve")
def approve(
    work_order_id: str,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
):
    try:
        return gateway.approve(
            _context(request, idempotency_key),
            work_order_id,
        )
    except Exception as exc:
        raise _translate_error(exc) from exc


@app.post("/api/v1/vs001/work-orders/{work_order_id}/execute")
def execute(
    work_order_id: str,
    body: ExecuteBody,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
):
    try:
        return gateway.execute(
            _context(request, idempotency_key),
            work_order_id,
            heading=body.heading,
            body=body.body,
        )
    except Exception as exc:
        raise _translate_error(exc) from exc


@app.post("/api/v1/vs001/work-orders/{work_order_id}/review")
def review(
    work_order_id: str,
    body: ReviewBody,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
):
    try:
        return gateway.review(
            _context(request, idempotency_key),
            work_order_id,
            decision=body.decision,
        )
    except Exception as exc:
        raise _translate_error(exc) from exc


@app.get("/api/v1/vs001/assets")
def list_assets(request: Request):
    try:
        return {
            "assets": gateway.list_assets(_context(request, "asset:read:list"))
        }
    except Exception as exc:
        raise _translate_error(exc) from exc


@app.get("/api/v1/vs001/assets/{asset_id}")
def get_asset(asset_id: str, request: Request):
    try:
        return gateway.get_asset(
            _context(request, f"asset:read:{asset_id}"),
            asset_id,
        )
    except Exception as exc:
        raise _translate_error(exc) from exc


@app.get("/api/v1/vs001/assets/{asset_id}/content")
def get_asset_content(asset_id: str, request: Request):
    try:
        return gateway.get_asset(
            _context(request, f"asset:content:{asset_id}"),
            asset_id,
            include_content=True,
        )
    except Exception as exc:
        raise _translate_error(exc) from exc


@app.post("/api/v1/vs001/assets/{asset_id}/approve")
def approve_asset(
    asset_id: str,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
):
    try:
        return gateway.approve_asset(
            _context(request, idempotency_key),
            asset_id,
        )
    except Exception as exc:
        raise _translate_error(exc) from exc


@app.get("/api/v1/vs001/demo-spine/offers")
def demo_spine_offers():
    return {"offers": demo_spine_store.list_offers()}


@app.post("/api/v1/vs001/demo-spine/runs")
def create_demo_spine_run(body: CreateDemoRunBody):
    try:
        return demo_spine_store.create_run(
            offer_id=body.offer_id,
            founder_goal=body.founder_goal,
        )
    except Exception as exc:
        raise _translate_error(exc) from exc


@app.get("/api/v1/vs001/demo-spine/runs")
def list_demo_spine_runs():
    return {"runs": demo_spine_store.list_runs()}


@app.get("/api/v1/vs001/demo-spine/runs/{demo_run_id}")
def get_demo_spine_run(demo_run_id: str):
    try:
        return demo_spine_store.get_run(demo_run_id)
    except Exception as exc:
        raise _translate_error(exc) from exc


@app.post("/api/v1/vs001/demo-spine/runs/{demo_run_id}/advance")
def advance_demo_spine_run(demo_run_id: str):
    try:
        return demo_spine_store.advance_run(demo_run_id)
    except Exception as exc:
        raise _translate_error(exc) from exc


@app.post("/api/v1/vs001/demo-spine/runs/{demo_run_id}/decision")
def decide_demo_spine_run(demo_run_id: str, body: DemoDecisionBody):
    try:
        return demo_spine_store.decide_run(demo_run_id, body.decision)
    except Exception as exc:
        raise _translate_error(exc) from exc


@app.get("/api/v1/vs001/real-workbench/templates")
def real_workbench_templates():
    try:
        with database.command_session() as session:
            return {"templates": RealWorkbenchStore(session).list_templates()}
    except Exception as exc:
        raise _translate_error(exc) from exc


@app.post("/api/v1/vs001/real-workbench/runs")
def create_real_workbench_run(body: CreateRealWorkbenchRunBody):
    try:
        with database.command_session() as session:
            return RealWorkbenchStore(session).create_run(
                product_line_id=body.product_line_id,
                founder_goal=body.founder_goal,
            )
    except Exception as exc:
        raise _translate_error(exc) from exc


@app.get("/api/v1/vs001/real-workbench/runs")
def list_real_workbench_runs():
    try:
        with database.command_session() as session:
            return {"runs": RealWorkbenchStore(session).list_runs()}
    except Exception as exc:
        raise _translate_error(exc) from exc


@app.get("/api/v1/vs001/real-workbench/runs/{run_id}")
def get_real_workbench_run(run_id: str):
    try:
        with database.command_session() as session:
            return RealWorkbenchStore(session).get_run(run_id)
    except Exception as exc:
        raise _translate_error(exc) from exc


__all__ = ["app"]
