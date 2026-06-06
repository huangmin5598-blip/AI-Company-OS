#!/usr/bin/env python3
"""
os-worker wrapper v0.46.5-B0R
Bootstrap version: simulates os-worker/local-script execution
Usage: python3 os-worker-wrapper.py <script_ref> <args_json>
"""
import sys
import os
import json
import subprocess
import hashlib
from datetime import datetime

WORK_QUEUE_BASE = os.path.expanduser("~/projects/ai-company-os/private/work-queue")

def sha256_file(path):
    """Compute SHA256 of a file."""
    if not os.path.exists(path):
        return "FILE_NOT_FOUND"
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def log(message):
    print(f"[os-worker] {message}", flush=True)

def execute_task(script_ref, args_json):
    log(f"Starting task: script_ref={script_ref}")
    log(f"Args: {args_json}")
    
    result = {
        "status": "unknown",
        "stdout": "",
        "stderr": "",
        "exit_code": -1,
        "execution_time_ms": 0
    }
    
    try:
        start = datetime.now()
        
        script_path = os.path.expanduser(f"~/projects/ai-company-os/{script_ref}")
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script not found: {script_path}")
        
        # Execute with python3 (not bash)
        proc = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        end = datetime.now()
        delta = (end - start).total_seconds() * 1000
        
        result["stdout"] = proc.stdout
        result["stderr"] = proc.stderr
        result["exit_code"] = proc.returncode
        result["execution_time_ms"] = int(delta)
        result["status"] = "done" if proc.returncode == 0 else "failed"
        
    except Exception as e:
        result["status"] = "failed"
        result["stderr"] = str(e)
    
    return result

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: os-worker-wrapper.py <script_ref> <args_json>")
        sys.exit(1)
    
    script_ref = sys.argv[1]
    args_json = sys.argv[2]
    
    result = execute_task(script_ref, args_json)
    print(json.dumps(result, ensure_ascii=False))
