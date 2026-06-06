#!/usr/bin/env python3
"""
local_script_worker.py
v0.46.5-B1-1 Local Script Worker Wrapper

职责：
- 从 inbox 认领任务
- 写入 claimed/running/waiting_review 状态
- 调用白名单脚本
- 写 outbox 结果
- 写 audit-log

通用设计：不硬编码任何具体任务。
"""
import sys
import os
import json
import yaml
import subprocess
import shutil
import hashlib
from datetime import datetime

WORKSPACE = os.path.expanduser("~/projects/ai-company-os")
WORK_QUEUE = os.path.join(WORKSPACE, "private/work-queue")
STATE_DIR = os.path.join(WORK_QUEUE, "state")

def sha256_file(path):
    if not os.path.exists(path):
        return "FILE_NOT_FOUND"
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def log(msg):
    print(f"[local_script_worker] {msg}", flush=True)

def load_task_abs(abs_path):
    with open(abs_path, "r") as f:
        return yaml.safe_load(f)

def save_task_abs(abs_path, task_data):
    with open(abs_path, "w") as f:
        yaml.dump(task_data, f, default_flow_style=False, allow_unicode=True)

def move_file_abs(src_abs, dest_dir_abs):
    os.makedirs(dest_dir_abs, exist_ok=True)
    dest_abs = os.path.join(dest_dir_abs, os.path.basename(src_abs))
    shutil.move(src_abs, dest_abs)
    return dest_abs

def write_audit_log(audit_entry):
    os.makedirs(STATE_DIR, exist_ok=True)
    audit_log_path = os.path.join(STATE_DIR, "audit-log.yaml")
    log_entries = []
    if os.path.exists(audit_log_path):
        with open(audit_log_path, "r") as f:
            log_entries = yaml.safe_load(f) or []
    log_entries.append(audit_entry)
    with open(audit_log_path, "w") as f:
        yaml.dump(log_entries, f, default_flow_style=False, allow_unicode=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: local_script_worker.py <task_file_relative_path>")
        sys.exit(1)
    
    task_rel = sys.argv[1]
    task_abs = os.path.join(WORKSPACE, task_rel)
    
    log(f"Starting worker for task: {task_rel}")
    
    # Load task
    task = load_task_abs(task_abs)
    work_id = task.get("work_id", "UNKNOWN")
    attempt_id = task.get("attempt_id", f"{work_id}-A1")
    worker_id = "os-worker-local-001"
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")
    lease_expires = (datetime.now().replace(hour=(datetime.now().hour + 1) % 24)).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    
    audit_transitions = []
    
    # Step 1: Claim
    task["claimed_by"] = "os-worker/local-script"
    task["claimed_at"] = now
    task["lease_expires_at"] = lease_expires
    task["worker_id"] = worker_id
    task["status"] = "claimed"
    save_task_abs(task_abs, task)
    claimed_dir = os.path.join(WORK_QUEUE, "claimed")
    task_abs = move_file_abs(task_abs, claimed_dir)
    log(f"Task claimed: {work_id} -> {task_abs}")
    
    audit_transitions.append({
        "transition": "inbox→claimed",
        "timestamp": now,
        "claimed_by": "os-worker/local-script",
        "attempt_id": attempt_id,
        "lease_expires_at": lease_expires
    })
    
    # Step 2: Start running
    task = load_task_abs(task_abs)
    now_running = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")
    task["started_at"] = now_running
    task["status"] = "running"
    save_task_abs(task_abs, task)
    running_dir = os.path.join(WORK_QUEUE, "running")
    task_abs = move_file_abs(task_abs, running_dir)
    log(f"Task running: {work_id} -> {task_abs}")
    
    audit_transitions.append({
        "transition": "claimed→running",
        "timestamp": now_running,
        "worker_id": worker_id
    })
    
    # Step 3: Execute whitelist script
    task = load_task_abs(task_abs)
    script_ref = task["task"]["script_ref"]
    args = task["task"]["args"]
    timeout = task["task"].get("timeout_seconds", 30)
    
    script_abs = os.path.join(WORKSPACE, script_ref)
    log(f"Executing whitelist script: {script_ref}")
    
    # Build command based on script_id
    cmd = ["python3", script_abs]
    
    script_id = task["task"].get("script_id", "")
    
    if script_id == "docs-frontmatter-add":
        # docs-frontmatter-add.py expects: version status last_updated [--dry-run] target_files...
        frontmatter = args.get("frontmatter_template", {})
        cmd.append(frontmatter.get("version", "v0.46.5"))
        cmd.append(frontmatter.get("status", "Active"))
        cmd.append(frontmatter.get("last_updated", datetime.now().strftime("%Y-%m-%d")))
        
        if args.get("dry_run", False):
            cmd.append("--dry-run")
        
        for f in args.get("target_files", []):
            cmd.append(f)
    
    elif script_id == "docs-frontmatter-check":
        # docs-frontmatter-check.py expects: target_paths...
        for p in args.get("target_paths", []):
            cmd.append(os.path.join(WORKSPACE, p))
    
    else:
        # Generic fallback
        for k, v in args.items():
            if isinstance(v, list):
                for item in v:
                    cmd.append(str(item))
            elif isinstance(v, str):
                cmd.append(v)
    
    log(f"Command: {' '.join(cmd)}")
    
    start = datetime.now()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=WORKSPACE)
        stdout = proc.stdout
        stderr = proc.stderr
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        stdout = ""
        stderr = "TIMEOUT"
        exit_code = 124
    end = datetime.now()
    execution_time_ms = int((end - start).total_seconds() * 1000)
    
    log(f"Script completed: exit_code={exit_code}, time={execution_time_ms}ms")
    
    # Step 4: Write outbox, move to waiting_review
    now_finished = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")
    
    # Determine output file based on phase
    phase = task.get("phase", "")
    if "B1-1A" in phase:
        output_ref = os.path.join("outbox", f"{work_id}-dry-run-result.json")
    else:
        output_ref = os.path.join("outbox", f"{work_id}-result.json")
    
    output_abs = os.path.join(WORKSPACE, output_ref)
    
    result = {
        "work_id": work_id,
        "attempt_id": attempt_id,
        "status": "done" if exit_code == 0 else "failed",
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        "execution_time_ms": execution_time_ms
    }
    
    os.makedirs(os.path.dirname(output_abs), exist_ok=True)
    with open(output_abs, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    task["finished_at"] = now_finished
    task["output_ref"] = output_ref
    task["status"] = "waiting_review"
    save_task_abs(task_abs, task)
    waiting_review_dir = os.path.join(WORK_QUEUE, "waiting_review")
    task_abs = move_file_abs(task_abs, waiting_review_dir)
    log(f"Task waiting_review: {work_id} -> {task_abs}")
    
    audit_transitions.append({
        "transition": "running→waiting_review",
        "timestamp": now_finished,
        "output_ref": output_ref
    })
    
    # Write audit log
    audit_entry = {
        "work_id": work_id,
        "attempt_id": attempt_id,
        "worker_id": worker_id,
        "timestamp": now_finished,
        "transitions": audit_transitions,
        "execution": {
            "script_ref": script_ref,
            "script_id": script_id,
            "exit_code": exit_code,
            "execution_time_ms": execution_time_ms,
            "stdout": stdout[:500],
            "stderr": stderr[:200]
        }
    }
    write_audit_log(audit_entry)
    
    log(f"Worker complete: {work_id}")
    print(json.dumps({
        "work_id": work_id,
        "status": "waiting_review",
        "output_ref": output_ref,
        "task_abs": task_abs,
        "audit_log_ref": "private/work-queue/state/audit-log.yaml"
    }))

if __name__ == "__main__":
    main()
