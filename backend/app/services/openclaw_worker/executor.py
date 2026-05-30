# @PRODUCT Service — v0.14 OpenClaw Worker — Task Executor
"""
Task Executor — executes safe task types for OpenClaw Worker.

Supported task types:
  - echo_test: Echo input context back. No LLM needed. Fastest test.
  - read_context_and_write_summary: Use local LLM to generate a summary
    of input context. Writes artifacts/<WO-ID>/summary.md.

Architecture:
  execute_task(task_card) → result manifest dict

  The executor is designed to be replaced:
  - echo_test → always works (no external deps)
  - read_context_and_write_summary → uses Ollama (localhost:11434)
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


# Supported task types
SUPPORTED_TASK_TYPES = {
    "echo_test",
    "read_context_and_write_summary",
    "file_analysis",
}

# Default LLM endpoint
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "deepseek-r1:8b")

# Base artifacts directory
BASE_ARTIFACTS_DIR = os.path.expanduser("~/.ai-company-os/artifacts")


def _artifact_dir(wo_id: str) -> str:
    return os.path.join(BASE_ARTIFACTS_DIR, wo_id)


def _ensure_dir(path: str) -> bool:
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError:
        return False


def _call_llm(prompt: str, system_prompt: str = "") -> Optional[str]:
    """Call Ollama generate API. Returns response text or None on error."""
    import urllib.request

    url = f"{OLLAMA_BASE_URL}/api/generate"
    body = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 1024},
    }).encode()

    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            return result.get("response", "").strip()
    except Exception as e:
        return None


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _build_result(
    wo_id: str,
    status: str,
    summary: str,
    artifacts: list,
    confidence: float,
    steps: list,
    errors: list,
    executor_name: str = "openclaw-worker-lite",
) -> dict:
    """Build a Result Manifest v1.1 dict."""
    return {
        "work_order_id": wo_id,
        "status": status,
        "result_summary": summary,
        "artifacts": artifacts,
        "confidence": confidence,
        "steps": steps,
        "started_at": steps[0].get("timestamp", _now_iso()) if steps else _now_iso(),
        "finished_at": _now_iso(),
        "executor": executor_name,
        "errors": errors,
    }


def execute_echo_test(task_card: dict) -> dict:
    """
    Echo test — simplest possible task.

    Reads input_context and echoes it back as result.
    No LLM, no external deps. For validating the execution pipeline.
    """
    wo_id = task_card.get("work_order_id", "unknown")
    context = task_card.get("context", task_card.get("input_context", ""))
    expected = task_card.get("expected_output", "")
    now = _now_iso()

    steps = [
        {"step": "read_task_card", "detail": f"Read task card for {wo_id}", "timestamp": now},
        {"step": "echo_test", "detail": f"Echoed {len(context)} chars of context", "timestamp": now},
    ]

    # Write output artifact
    artifacts_dir = _artifact_dir(wo_id)
    _ensure_dir(artifacts_dir)

    output_path = os.path.join(artifacts_dir, "echo_output.txt")
    output_content = (
        f"=== Echo Test Result ===\n"
        f"Work Order: {wo_id}\n"
        f"Expected Output: {expected}\n"
        f"Input Context ({len(context)} chars):\n"
        f"{'─'*40}\n"
        f"{context}\n"
        f"{'─'*40}\n"
        f"Echo completed at: {now}\n"
    )
    Path(output_path).write_text(output_content, encoding="utf-8")

    artifacts = [
        {"name": "echo_output.txt", "path": output_path, "type": "text"},
    ]

    return _build_result(
        wo_id=wo_id,
        status="completed",
        summary=f"Echo test completed. Read {len(context)} chars of context. Output written to echo_output.txt.",
        artifacts=artifacts,
        confidence=1.0,
        steps=steps,
        errors=[],
    )


def execute_read_context_and_write_summary(task_card: dict) -> dict:
    """
    Read context and write a summary using local LLM.

    This is the primary "real" task type for v0.14 MVP.
    Uses Ollama (localhost:11434) to generate a structured summary.
    """
    wo_id = task_card.get("work_order_id", "unknown")
    context = task_card.get("context", task_card.get("input_context", ""))
    expected = task_card.get("expected_output", "")
    now = _now_iso()

    steps = [
        {"step": "read_task_card", "detail": f"Read task card for {wo_id}", "timestamp": now},
    ]

    if not context:
        return _build_result(
            wo_id=wo_id,
            status="failed",
            summary="No input context provided. Cannot generate summary.",
            artifacts=[],
            confidence=0.0,
            steps=steps,
            errors=["Empty input_context"],
        )

    steps.append({"step": "call_llm", "detail": f"Calling LLM ({OLLAMA_MODEL}) for summary", "timestamp": _now_iso()})

    # Build prompt
    system_prompt = (
        "你是一个专业的 AI 助手。请根据提供的上下文生成一份结构化摘要。\n"
        "输出格式：\n"
        "1. 核心要点（3-5 点）\n"
        "2. 关键发现\n"
        "3. 建议下一步"
    )
    user_prompt = f"请为以下内容生成结构化摘要：\n\n{context}\n\n---\n预期输出：{expected}"

    llm_response = _call_llm(prompt=user_prompt, system_prompt=system_prompt)

    if llm_response is None:
        # Fallback: generate a simple summary without LLM
        summary_text = (
            f"# Summary for {wo_id}\n\n"
            f"**Context length:** {len(context)} chars\n\n"
            f"**Content preview (first 200 chars):**\n"
            f"{context[:200]}...\n\n"
            f"*(LLM unavailable — this is a template-based fallback summary)*\n"
        )
        confidence = 0.3
        errors = [f"LLM ({OLLAMA_MODEL}@{OLLAMA_BASE_URL}) unavailable — used template fallback"]
        steps.append({"step": "llm_unavailable", "detail": errors[-1], "timestamp": _now_iso()})
    else:
        summary_text = (
            f"# Summary for {wo_id}\n\n"
            f"**Generated by:** {OLLAMA_MODEL}\n"
            f"**Date:** {_now_iso()}\n\n"
            f"{llm_response}\n"
        )
        confidence = 0.82
        errors = []
        steps.append({"step": "llm_completed", "detail": f"LLM generated {len(llm_response)} chars", "timestamp": _now_iso()})

    # Write output artifact
    artifacts_dir = _artifact_dir(wo_id)
    _ensure_dir(artifacts_dir)

    output_path = os.path.join(artifacts_dir, "summary.md")
    Path(output_path).write_text(summary_text, encoding="utf-8")

    artifacts = [
        {"name": "summary.md", "path": output_path, "type": "markdown"},
    ]

    return _build_result(
        wo_id=wo_id,
        status="completed",
        summary=f"Summary generated via {OLLAMA_MODEL}. {len(summary_text)} chars written to summary.md.",
        artifacts=artifacts,
        confidence=confidence,
        steps=steps,
        errors=errors,
    )


def execute_file_analysis(task_card: dict) -> dict:
    """
    File analysis — read a file specified in input_context and analyze it.
    Limited to safe file types (.txt, .md, .csv, .json).
    """
    wo_id = task_card.get("work_order_id", "unknown")
    context = task_card.get("context", task_card.get("input_context", ""))
    now = _now_iso()

    steps = [
        {"step": "read_task_card", "detail": f"Read task card for {wo_id}", "timestamp": now},
    ]

    # Extract file path from context
    # Format: "file: /path/to/file.txt"
    file_path = None
    for line in context.split("\n"):
        line = line.strip()
        if line.startswith("file:"):
            file_path = line[5:].strip()
            break

    if not file_path or not os.path.exists(file_path):
        return _build_result(
            wo_id=wo_id,
            status="failed",
            summary="File not found. Provide a valid file path with 'file: /path/to/file' in input_context.",
            artifacts=[],
            confidence=0.0,
            steps=steps,
            errors=[f"File not found: {file_path}"],
        )

    # Safety: only allow safe file extensions
    safe_extensions = {".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".log", ".py", ".js", ".ts", ".html", ".css"}
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in safe_extensions:
        return _build_result(
            wo_id=wo_id,
            status="failed",
            summary=f"File type '{ext}' is not in safe allowlist.",
            artifacts=[],
            confidence=0.0,
            steps=steps,
            errors=[f"Unsafe file extension: {ext}. Allowed: {sorted(safe_extensions)}"],
        )

    # Read the file
    try:
        content = Path(file_path).read_text(encoding="utf-8")
    except Exception as e:
        return _build_result(
            wo_id=wo_id,
            status="failed",
            summary=f"Failed to read file: {e}",
            artifacts=[],
            confidence=0.0,
            steps=steps,
            errors=[str(e)],
        )

    steps.append({"step": "read_file", "detail": f"Read {len(content)} chars from {file_path}", "timestamp": _now_iso()})

    # Use LLM to analyze
    llm_prompt = (
        f"请分析以下文件内容。文件路径：{file_path}\n\n"
        f"请提供：\n1. 文件概述\n2. 关键信息\n3. 文件大小和结构分析\n\n"
        f"文件内容（前 3000 字符）：\n\n{content[:3000]}"
    )

    llm_response = _call_llm(prompt=llm_prompt)
    if llm_response is None:
        llm_response = f"**File:** {file_path}\n**Size:** {len(content)} chars\n**Lines:** {content.count(chr(10)) + 1}\n*(LLM unavailable — basic stats only)*"

    # Write analysis
    artifacts_dir = _artifact_dir(wo_id)
    _ensure_dir(artifacts_dir)
    output_path = os.path.join(artifacts_dir, "file_analysis.md")
    analysis = (
        f"# File Analysis: {os.path.basename(file_path)}\n\n"
        f"**Generated by:** {OLLAMA_MODEL}\n"
        f"**Date:** {_now_iso()}\n\n"
        f"{llm_response}\n"
    )
    Path(output_path).write_text(analysis, encoding="utf-8")

    return _build_result(
        wo_id=wo_id,
        status="completed",
        summary=f"File analyzed: {os.path.basename(file_path)} ({len(content)} chars)",
        artifacts=[{"name": "file_analysis.md", "path": output_path, "type": "markdown"}],
        confidence=0.82 if llm_response else 0.4,
        steps=steps + [{"step": "llm_analysis", "detail": "Generated analysis", "timestamp": _now_iso()}],
        errors=[],
    )


# ── Task Type Dispatch ──

EXECUTOR_MAP = {
    "echo_test": execute_echo_test,
    "read_context_and_write_summary": execute_read_context_and_write_summary,
    "file_analysis": execute_file_analysis,
}


def execute_task(task_card: dict) -> dict:
    """
    Execute a task based on its task_type.

    Args:
        task_card: dict with at least 'task_type' and 'work_order_id'.

    Returns:
        Result Manifest dict (v1.1)
    """
    task_type = task_card.get("task_type", "")

    handler = EXECUTOR_MAP.get(task_type)
    if not handler:
        wo_id = task_card.get("work_order_id", "unknown")
        return _build_result(
            wo_id=wo_id,
            status="failed",
            summary=f"Unsupported task type: '{task_type}'. Supported: {', '.join(sorted(SUPPORTED_TASK_TYPES))}",
            artifacts=[],
            confidence=0.0,
            steps=[{"step": "validate", "detail": f"Unknown task type: {task_type}", "timestamp": _now_iso()}],
            errors=[f"Unsupported task type: {task_type}"],
        )

    try:
        return handler(task_card)
    except Exception as e:
        wo_id = task_card.get("work_order_id", "unknown")
        return _build_result(
            wo_id=wo_id,
            status="failed",
            summary=f"Execution error: {str(e)[:200]}",
            artifacts=[],
            confidence=0.0,
            steps=[{"step": "execute", "detail": str(e), "timestamp": _now_iso()}],
            errors=[str(e)],
        )
