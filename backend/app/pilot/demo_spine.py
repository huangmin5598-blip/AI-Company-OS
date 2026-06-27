"""Pilot-only deterministic multi-product-line workbench.

This module is intentionally not a scheduler, worker pool, runtime adapter, or
Agent Host. It gives Founder Control Center a local non-authoritative workbench
for parallel-looking offer streams without touching operational authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from typing import Literal

from app.pilot.demo_scenarios import (
    DEMO_MODE,
    DEMO_SOURCE_PATH,
    OFFERS,
    OFFERS_BY_ID,
    PILOT_AUTHORITY,
    DemoOffer,
    DemoTaskTemplate,
)


TaskStatus = Literal["planned", "queued", "running", "waiting_review", "done"]
RunStatus = Literal["planned", "active", "ready_for_decision", "go", "no_go"]
FounderDecision = Literal["go", "no_go"]

TASK_STATUS_SEQUENCE: tuple[TaskStatus, ...] = (
    "planned",
    "queued",
    "running",
    "waiting_review",
    "done",
)


@dataclass
class DemoTask:
    task_id: str
    title: str
    executor_slot: str
    status: TaskStatus
    expected_output: str
    audit_summary: str


@dataclass
class DemoReplayEvent:
    event_id: str
    event_type: str
    title: str
    summary: str
    actor: str
    created_at: str


@dataclass
class DemoAsset:
    asset_id: str
    title: str
    content_markdown: str
    authority: str = PILOT_AUTHORITY
    visibility: str = "restricted"
    public_safe: bool = False


@dataclass
class DemoRun:
    demo_run_id: str
    offer_id: str
    founder_goal: str
    status: RunStatus
    created_at: str
    updated_at: str
    tasks: list[DemoTask]
    replay: list[DemoReplayEvent]
    final_asset: DemoAsset | None = None
    founder_decision: FounderDecision | None = None
    authority: str = PILOT_AUTHORITY
    mode: str = DEMO_MODE
    source_path: str = DEMO_SOURCE_PATH


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _event(
    run_id: str,
    event_type: str,
    title: str,
    summary: str,
    actor: str,
) -> DemoReplayEvent:
    created_at = _now()
    return DemoReplayEvent(
        event_id=_stable_id("evt", run_id, event_type, title, created_at),
        event_type=event_type,
        title=title,
        summary=summary,
        actor=actor,
        created_at=created_at,
    )


def _task(run_id: str, index: int, template: DemoTaskTemplate) -> DemoTask:
    return DemoTask(
        task_id=_stable_id("dtask", run_id, str(index), template.title),
        title=template.title,
        executor_slot=template.executor_slot,
        status="planned",
        expected_output=template.expected_output,
        audit_summary=template.audit_summary,
    )


def _run_envelope(run: DemoRun, offer: DemoOffer) -> dict[str, object]:
    return {
        "demo_run_id": run.demo_run_id,
        "offer": {
            "offer_id": offer.offer_id,
            "display_name": offer.display_name,
            "tagline": offer.tagline,
        },
        "founder_goal": run.founder_goal,
        "status": run.status,
        "authority": run.authority,
        "mode": run.mode,
        "source_path": run.source_path,
        "created_at": run.created_at,
        "updated_at": run.updated_at,
        "tasks": [task.__dict__ for task in run.tasks],
        "replay": [event.__dict__ for event in run.replay],
        "final_asset": (
            {
                "asset_id": run.final_asset.asset_id,
                "title": run.final_asset.title,
                "content_markdown": run.final_asset.content_markdown,
                "authority": run.final_asset.authority,
                "visibility": run.final_asset.visibility,
                "public_safe": run.final_asset.public_safe,
            }
            if run.final_asset is not None
            else None
        ),
        "founder_decision": run.founder_decision,
        "governance": {
            "authority": PILOT_AUTHORITY,
            "mode": DEMO_MODE,
            "pilot_only": True,
            "operational_authority": False,
            "real_runtime_invoked": False,
            "public_safe": False,
        },
    }


class DemoSpineStore:
    """In-memory pilot store for deterministic demo runs."""

    def __init__(self) -> None:
        self._runs: dict[str, DemoRun] = {}

    def list_offers(self) -> list[dict[str, str]]:
        return [
            {
                "offer_id": offer.offer_id,
                "display_name": offer.display_name,
                "tagline": offer.tagline,
                "default_goal": offer.default_goal,
            }
            for offer in OFFERS
        ]

    def create_run(self, offer_id: str, founder_goal: str) -> dict[str, object]:
        offer = self._offer(offer_id)
        goal = founder_goal.strip()
        if not goal:
            raise ValueError("founder_goal_required")
        created_at = _now()
        run_id = _stable_id("drun", offer_id, goal, created_at)
        tasks = [
            _task(run_id, index, template)
            for index, template in enumerate(offer.tasks, start=1)
        ]
        run = DemoRun(
            demo_run_id=run_id,
            offer_id=offer.offer_id,
            founder_goal=goal,
            status="planned",
            created_at=created_at,
            updated_at=created_at,
            tasks=tasks,
            replay=[
                _event(
                    run_id,
                    "founder.goal_submitted",
                    "Founder submitted goal",
                    goal,
                    "founder",
                ),
                _event(
                    run_id,
                    "ceo_agent.tasks_decomposed",
                    "CEO Agent decomposed tasks",
                    f"{len(tasks)} deterministic tasks prepared for {offer.display_name}.",
                    "ceo_agent_slot",
                ),
            ],
        )
        self._runs[run_id] = run
        return _run_envelope(run, offer)

    def list_runs(self) -> list[dict[str, object]]:
        return [
            _run_envelope(run, self._offer(run.offer_id))
            for run in sorted(
                self._runs.values(),
                key=lambda item: item.created_at,
                reverse=True,
            )
        ]

    def get_run(self, demo_run_id: str) -> dict[str, object]:
        run = self._run(demo_run_id)
        return _run_envelope(run, self._offer(run.offer_id))

    def advance_run(self, demo_run_id: str) -> dict[str, object]:
        run = self._run(demo_run_id)
        if run.status in {"go", "no_go"}:
            raise ValueError("demo_run_already_decided")
        task = self._next_advancable_task(run)
        if task is None:
            self._ensure_asset(run)
            run.status = "ready_for_decision"
            run.updated_at = _now()
            return _run_envelope(run, self._offer(run.offer_id))

        current_index = TASK_STATUS_SEQUENCE.index(task.status)
        task.status = TASK_STATUS_SEQUENCE[current_index + 1]
        run.status = "active"
        run.updated_at = _now()
        run.replay.append(
            _event(
                run.demo_run_id,
                f"task.{task.status}",
                task.title,
                f"{task.executor_slot}: {task.audit_summary}",
                task.executor_slot,
            )
        )
        if all(item.status == "done" for item in run.tasks):
            self._ensure_asset(run)
            run.status = "ready_for_decision"
        return _run_envelope(run, self._offer(run.offer_id))

    def decide_run(
        self,
        demo_run_id: str,
        decision: FounderDecision,
    ) -> dict[str, object]:
        run = self._run(demo_run_id)
        if decision not in {"go", "no_go"}:
            raise ValueError("invalid_founder_decision")
        if run.status != "ready_for_decision":
            raise ValueError("demo_run_not_ready_for_decision")
        run.founder_decision = decision
        run.status = decision
        run.updated_at = _now()
        run.replay.append(
            _event(
                run.demo_run_id,
                f"founder.{decision}",
                f"Founder decided {decision.upper()}",
                (
                    "Founder accepted this demo stream for the next validation step."
                    if decision == "go"
                    else "Founder rejected this demo stream for now."
                ),
                "founder",
            )
        )
        return _run_envelope(run, self._offer(run.offer_id))

    def reset(self) -> None:
        self._runs.clear()

    def _offer(self, offer_id: str) -> DemoOffer:
        try:
            return OFFERS_BY_ID[offer_id]
        except KeyError as exc:
            raise LookupError("demo_offer_not_found") from exc

    def _run(self, demo_run_id: str) -> DemoRun:
        try:
            return self._runs[demo_run_id]
        except KeyError as exc:
            raise LookupError("demo_run_not_found") from exc

    def _next_advancable_task(self, run: DemoRun) -> DemoTask | None:
        for task in run.tasks:
            if task.status != "done":
                return task
        return None

    def _ensure_asset(self, run: DemoRun) -> None:
        if run.final_asset is not None:
            return
        offer = self._offer(run.offer_id)
        content = offer.final_asset_template.format(goal=run.founder_goal)
        run.final_asset = DemoAsset(
            asset_id=_stable_id("dasset", run.demo_run_id, offer.final_asset_title),
            title=offer.final_asset_title,
            content_markdown=content,
        )
        run.replay.append(
            _event(
                run.demo_run_id,
                "asset.archived",
                "Final demo asset archived",
                (
                    f"{offer.final_asset_title} created as restricted "
                    "pilot_non_authoritative demo material."
                ),
                "asset_center_pilot",
            )
        )


__all__ = [
    "DEMO_MODE",
    "DEMO_SOURCE_PATH",
    "PILOT_AUTHORITY",
    "DemoSpineStore",
]
