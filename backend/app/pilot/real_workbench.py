"""Pilot-only persistent Founder Control Center workbench.

RS1-A turns the previous in-memory demo spine into a small persistent pilot
surface. It is deliberately not a scheduler, worker pool, runtime adapter, or
agent host: product-line tasks are planned and stored, never executed here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Literal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.pilot.database import PILOT_AUTHORITY
from app.pilot.demo_scenarios import OFFERS, OFFERS_BY_ID, DemoOffer


REAL_WORKBENCH_MODE = "real_workbench_pilot"
REAL_WORKBENCH_SOURCE_PATH = "founder_control_center_real_workbench"
REAL_WORKBENCH_SCHEMA_COMPONENT = "real_workbench"
REAL_WORKBENCH_SCHEMA_VERSION = "rs1a-1"

RunStatus = Literal["planned", "active", "ready_for_decision", "go", "no_go"]
TaskStatus = Literal["planned"]


@dataclass(frozen=True)
class WorkbenchTemplate:
    product_line_id: str
    display_name: str
    tagline: str
    default_goal: str
    task_count: int


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def list_product_line_templates() -> list[dict[str, object]]:
    return [
        {
            "product_line_id": offer.offer_id,
            "display_name": offer.display_name,
            "tagline": offer.tagline,
            "default_goal": offer.default_goal,
            "task_count": len(offer.tasks),
            "authority": PILOT_AUTHORITY,
            "mode": REAL_WORKBENCH_MODE,
        }
        for offer in OFFERS
    ]


def _task_plan_hash(tasks: list[dict[str, object]]) -> str:
    payload = json.dumps(tasks, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _task_envelopes(run_id: str, offer: DemoOffer, created_at: str) -> list[dict[str, object]]:
    tasks: list[dict[str, object]] = []
    for index, template in enumerate(offer.tasks, start=1):
        tasks.append(
            {
                "task_id": _stable_id("rwtsk", run_id, str(index), template.title),
                "step_index": index,
                "title": template.title,
                "executor_slot": template.executor_slot,
                "status": "planned",
                "expected_output": template.expected_output,
                "audit_summary": template.audit_summary,
                "authority": PILOT_AUTHORITY,
                "created_at": created_at,
            }
        )
    return tasks


def _governance() -> dict[str, object]:
    return {
        "authority": PILOT_AUTHORITY,
        "mode": REAL_WORKBENCH_MODE,
        "pilot_only": True,
        "operational_authority": False,
        "real_runtime_invoked": False,
        "scheduler_invoked": False,
        "worker_pool_invoked": False,
        "public_safe": False,
    }


class RealWorkbenchStore:
    """Session-scoped persistent pilot workbench store."""

    def __init__(self, session: Session):
        self.session = session

    def list_templates(self) -> list[dict[str, object]]:
        return list_product_line_templates()

    def create_run(self, product_line_id: str, founder_goal: str) -> dict[str, object]:
        offer = self._offer(product_line_id)
        goal = founder_goal.strip()
        if not goal:
            raise ValueError("founder_goal_required")
        created_at = _now()
        run_id = _stable_id("rwr", product_line_id, goal, created_at)
        tasks = _task_envelopes(run_id, offer, created_at)
        task_plan_hash = _task_plan_hash(tasks)
        self.session.execute(
            text(
                "INSERT INTO pilot_workbench_runs"
                " (run_id, product_line_id, founder_goal, status, authority,"
                " mode, source_path, task_plan_hash, created_at, updated_at)"
                " VALUES"
                " (:run_id, :product_line_id, :founder_goal, 'planned',"
                " :authority, :mode, :source_path, :task_plan_hash,"
                " :created_at, :updated_at)"
            ),
            {
                "run_id": run_id,
                "product_line_id": product_line_id,
                "founder_goal": goal,
                "authority": PILOT_AUTHORITY,
                "mode": REAL_WORKBENCH_MODE,
                "source_path": REAL_WORKBENCH_SOURCE_PATH,
                "task_plan_hash": task_plan_hash,
                "created_at": created_at,
                "updated_at": created_at,
            },
        )
        for task in tasks:
            self.session.execute(
                text(
                    "INSERT INTO pilot_workbench_tasks"
                    " (task_id, run_id, step_index, title, executor_slot,"
                    " status, expected_output, audit_summary, authority,"
                    " created_at)"
                    " VALUES"
                    " (:task_id, :run_id, :step_index, :title,"
                    " :executor_slot, :status, :expected_output,"
                    " :audit_summary, :authority, :created_at)"
                ),
                {**task, "run_id": run_id},
            )
        return self.get_run(run_id)

    def list_runs(self) -> list[dict[str, object]]:
        rows = self.session.execute(
            text(
                "SELECT run_id FROM pilot_workbench_runs"
                " ORDER BY created_at DESC, run_id DESC"
            )
        ).scalars()
        return [self.get_run(run_id) for run_id in rows]

    def get_run(self, run_id: str) -> dict[str, object]:
        row = self.session.execute(
            text(
                "SELECT run_id, product_line_id, founder_goal, status,"
                " authority, mode, source_path, task_plan_hash,"
                " created_at, updated_at"
                " FROM pilot_workbench_runs WHERE run_id=:run_id"
            ),
            {"run_id": run_id},
        ).mappings().first()
        if row is None:
            raise LookupError("real_workbench_run_not_found")
        tasks = [
            dict(task)
            for task in self.session.execute(
                text(
                    "SELECT task_id, step_index, title, executor_slot,"
                    " status, expected_output, audit_summary, authority,"
                    " created_at"
                    " FROM pilot_workbench_tasks"
                    " WHERE run_id=:run_id ORDER BY step_index ASC"
                ),
                {"run_id": run_id},
            ).mappings()
        ]
        if _task_plan_hash(tasks) != row["task_plan_hash"]:
            raise RuntimeError("real_workbench_task_plan_hash_mismatch")
        offer = self._offer(row["product_line_id"])
        return {
            "run_id": row["run_id"],
            "product_line": {
                "product_line_id": offer.offer_id,
                "display_name": offer.display_name,
                "tagline": offer.tagline,
            },
            "founder_goal": row["founder_goal"],
            "status": row["status"],
            "authority": row["authority"],
            "mode": row["mode"],
            "source_path": row["source_path"],
            "task_plan_hash": row["task_plan_hash"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "task_plan": tasks,
            "governance": _governance(),
        }

    def _offer(self, product_line_id: str) -> DemoOffer:
        try:
            return OFFERS_BY_ID[product_line_id]
        except KeyError as exc:
            raise LookupError("real_workbench_product_line_not_found") from exc


__all__ = [
    "REAL_WORKBENCH_MODE",
    "REAL_WORKBENCH_SCHEMA_COMPONENT",
    "REAL_WORKBENCH_SCHEMA_VERSION",
    "REAL_WORKBENCH_SOURCE_PATH",
    "RealWorkbenchStore",
    "list_product_line_templates",
]
