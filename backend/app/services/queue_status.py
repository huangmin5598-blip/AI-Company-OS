"""v0.17.1 — OpenClaw Queue Status Check.

Scans the inbox/working/artifacts directories to surface
the real state of the task queue in CEO Briefs.

Detects:
  - Unclaimed tasks (in inbox)
  - Stale tasks (in working longer than STALE_THRESHOLD)
  - Completed tasks (artifacts with result.json)
"""

import os
import time
from dataclasses import dataclass, field
from typing import Optional

# Default OpenClaw directories
_INBOX_DIR = os.path.expanduser("~/.ai-company-os/openclaw/inbox")
_WORKING_DIR = os.path.expanduser("~/.ai-company-os/openclaw/working")
_ARTIFACTS_DIR = os.path.expanduser("~/.ai-company-os/artifacts")

# A task in working/ older than this is considered stale
STALE_THRESHOLD_SECONDS = 600  # 10 minutes


@dataclass
class QueueStatus:
    inbox_count: int = 0
    working_count: int = 0
    artifacts_completed: int = 0
    stale_working_count: int = 0
    unclaimed: list[str] = field(default_factory=list)
    stale_tasks: list[str] = field(default_factory=list)

    def any_issues(self) -> bool:
        return self.inbox_count > 0 or self.stale_working_count > 0

    def to_brief_section(self) -> str:
        """Format queue status as a CEO Brief section."""
        lines = []
        lines.append(f"- **Inbox:** {self.inbox_count}")
        lines.append(f"- **Working:** {self.working_count}")
        lines.append(f"- **Completed (artifacts):** {self.artifacts_completed}")
        lines.append(f"- **Stale working:** {self.stale_working_count}")

        if self.inbox_count > 0:
            lines.append("")
            lines.append("> ⚠️ **Unclaimed tasks detected.** Task cards were dispatched to OpenClaw")
            lines.append("> inbox but no worker has claimed them.")
            lines.append(">")
            lines.append("> **Suggested action:**")
            lines.append("> ```")
            lines.append("> cd ~/Documents/Codex/ai-company-os/backend")
            lines.append("> python3 ../bin/openclaw_worker.py --all --call-backend")
            lines.append("> ```")
            for task_id in self.unclaimed[:3]:
                lines.append(f">   • `{task_id}`")
            if len(self.unclaimed) > 3:
                lines.append(f">   • ... and {len(self.unclaimed) - 3} more")

        if self.stale_working_count > 0:
            lines.append("")
            lines.append("> ⚠️ **Stale working tasks detected.** These tasks were claimed by a")
            lines.append("> worker but never completed. They may be orphaned.")
            for task_id in self.stale_tasks[:3]:
                lines.append(f">   • `{task_id}`")
            if len(self.stale_tasks) > 3:
                lines.append(f">   • ... and {len(self.stale_tasks) - 3} more")

        return "\n".join(lines)


def _count_files(directory: str, suffix: str = ".task.json") -> int:
    """Count files in a directory with the given suffix."""
    if not os.path.isdir(directory):
        return 0
    return sum(1 for f in os.listdir(directory) if f.endswith(suffix))


def _list_files(directory: str, suffix: str = ".task.json") -> list[str]:
    """List files in a directory with the given suffix."""
    if not os.path.isdir(directory):
        return []
    return sorted(f for f in os.listdir(directory) if f.endswith(suffix))


def _count_artifacts_with_results() -> int:
    """Count artifacts directories that contain a result.json."""
    if not os.path.isdir(_ARTIFACTS_DIR):
        return 0
    count = 0
    for entry in os.listdir(_ARTIFACTS_DIR):
        result_path = os.path.join(_ARTIFACTS_DIR, entry, "result.json")
        if os.path.isfile(result_path):
            count += 1
    return count


def _find_stale_tasks() -> list[str]:
    """Find tasks in working/ that are older than STALE_THRESHOLD."""
    if not os.path.isdir(_WORKING_DIR):
        return []
    now = time.time()
    stale = []
    for f in _list_files(_WORKING_DIR, ".task.json"):
        path = os.path.join(_WORKING_DIR, f)
        age = now - os.path.getmtime(path)
        if age > STALE_THRESHOLD_SECONDS:
            stale.append(f.replace(".task.json", ""))
    return stale


def check_queue_status() -> QueueStatus:
    """Scan OpenClaw directories and return current queue status."""
    inbox_files = _list_files(_INBOX_DIR)
    working_files = _list_files(_WORKING_DIR)
    stale_tasks = _find_stale_tasks()

    return QueueStatus(
        inbox_count=len(inbox_files),
        working_count=len(working_files),
        artifacts_completed=_count_artifacts_with_results(),
        stale_working_count=len(stale_tasks),
        unclaimed=[f.replace(".task.json", "") for f in inbox_files],
        stale_tasks=stale_tasks,
    )
