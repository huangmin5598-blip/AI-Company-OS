#!/usr/bin/env python3
"""
checkpoint-resume-v1 — Auto Checkpoint Generator
在每个阶段完成后自动生成 checkpoint
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path("/Users/tangbomao/.openclaw/workspace/novel-v1")
CHECKPOINT_DIR = PROJECT_DIR / "checkpoints"

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

def load_task_card(task_id):
    """读取 Task Card"""
    card_file = PROJECT_DIR / "TASK-CARDS" / f"{task_id}-task-card.md"
    if card_file.exists():
        with open(card_file) as f:
            content = f.read()
        # 提取标题
        title = "Unknown"
        for line in content.split('\n'):
            if line.startswith('#'):
                title = line.replace('#', '').strip()
                break
        return title, str(card_file)
    return None, None

def load_outline(task_id):
    """读取大纲"""
    outline_file = PROJECT_DIR / "outlines" / f"{task_id}-outline.md"
    if outline_file.exists():
        return str(outline_file)
    return None

def load_manuscript(task_id):
    """读取正文"""
    # 查找今日 manuscripts
    today = datetime.now().strftime("%Y-%m-%d")
    ms_dir = PROJECT_DIR / "manuscripts" / today
    if ms_dir.exists():
        for f in ms_dir.glob(f"{task_id}-*.md"):
            return str(f)
    return None

def generate_task_init_checkpoint(task_id):
    """生成 task_init_checkpoint"""
    title, payload_ref = load_task_card(task_id)
    if not title:
        print(f"⚠️ Task Card not found for {task_id}")
        return None
    
    checkpoint = {
        "checkpoint_id": f"{task_id}-task-init-{get_timestamp()}",
        "project_id": "novel-v1",
        "task_id": task_id,
        "stage": "task_init",
        "checkpoint_type": "task_init_checkpoint",
        "payload_ref": payload_ref,
        "progress_pct": 5,
        "created_by": "lead-novel",
        "created_at": f"{datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')}",
        "next_agent": "story-editor",
        "resume_from": "task_created",
        "is_latest": True,
        "validation_status": "valid"
    }
    
    # 保存
    out_dir = CHECKPOINT_DIR / "task-init"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{checkpoint['checkpoint_id']}.json"
    with open(out_file, 'w') as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)
    
    print(f"✅ task_init_checkpoint: {checkpoint['checkpoint_id']}")
    return checkpoint

def generate_structure_checkpoint(task_id):
    """生成 structure_checkpoint"""
    payload_ref = load_outline(task_id)
    if not payload_ref:
        print(f"⚠️ Outline not found for {task_id}")
        return None
    
    checkpoint = {
        "checkpoint_id": f"{task_id}-structure-{get_timestamp()}",
        "project_id": "novel-v1",
        "task_id": task_id,
        "stage": "structure_ready",
        "checkpoint_type": "structure_checkpoint",
        "payload_ref": payload_ref,
        "progress_pct": 30,
        "created_by": "story-editor",
        "created_at": f"{datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')}",
        "next_agent": "writer",
        "resume_from": "outline_completed",
        "is_latest": True,
        "validation_status": "valid"
    }
    
    # 保存
    out_dir = CHECKPOINT_DIR / "structure"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{checkpoint['checkpoint_id']}.json"
    with open(out_file, 'w') as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)
    
    print(f"✅ structure_checkpoint: {checkpoint['checkpoint_id']}")
    return checkpoint

def generate_draft_progress_checkpoint(task_id, current_scene_id="chapter_1", completed_scenes=None, word_count=0):
    """生成 draft_progress_checkpoint"""
    payload_ref = load_manuscript(task_id)
    if not payload_ref:
        print(f"⚠️ Manuscript not found for {task_id}")
        return None
    
    if completed_scenes is None:
        completed_scenes = []
    
    checkpoint = {
        "checkpoint_id": f"{task_id}-draft-{get_timestamp()}",
        "project_id": "novel-v1",
        "task_id": task_id,
        "stage": "drafting",
        "checkpoint_type": "draft_progress_checkpoint",
        "payload_ref": payload_ref,
        "current_scene_id": current_scene_id,
        "completed_scene_ids": completed_scenes,
        "current_word_count": word_count,
        "next_resume_point": current_scene_id,
        "progress_pct": min(80, 30 + len(completed_scenes) * 10),
        "created_by": "writer",
        "created_at": f"{datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')}",
        "next_agent": "writer",
        "resume_from": current_scene_id,
        "is_latest": True,
        "validation_status": "valid"
    }
    
    # 保存
    out_dir = CHECKPOINT_DIR / "draft-progress"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{checkpoint['checkpoint_id']}.json"
    with open(out_file, 'w') as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)
    
    print(f"✅ draft_progress_checkpoint: {checkpoint['checkpoint_id']}")
    return checkpoint

def find_latest_checkpoint(task_id, checkpoint_type=None):
    """查找最近的 checkpoint"""
    checkpoint_types = [checkpoint_type] if checkpoint_type else ["task-init", "structure", "draft-progress"]
    
    for cp_type in checkpoint_types:
        cp_dir = CHECKPOINT_DIR / cp_type
        if not cp_dir.exists():
            continue
        
        # 查找匹配的 checkpoint
        candidates = list(cp_dir.glob(f"{task_id}-*.json"))
        if candidates:
            # 返回最新的
            latest = max(candidates, key=lambda p: p.stat().st_mtime)
            with open(latest) as f:
                return json.load(f)
    
    return None

def resume_from_checkpoint(task_id):
    """从 checkpoint 恢复"""
    checkpoint = find_latest_checkpoint(task_id)
    if not checkpoint:
        print(f"⚠️ No checkpoint found for {task_id}")
        return None
    
    stage = checkpoint.get("stage")
    checkpoint_type = checkpoint.get("checkpoint_type")
    resume_from = checkpoint.get("resume_from")
    payload_ref = checkpoint.get("payload_ref")
    
    print(f"📍 Found checkpoint: {checkpoint.get('checkpoint_id')}")
    print(f"   Stage: {stage}")
    print(f"   Type: {checkpoint_type}")
    print(f"   Resume from: {resume_from}")
    print(f"   Payload: {payload_ref}")
    
    return checkpoint

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python3 checkpoint_gen.py gen-task-init <task_id>")
        print("  python3 checkpoint_gen.py gen-structure <task_id>")
        print("  python3 checkpoint_gen.py gen-draft <task_id> [scene_id] [word_count]")
        print("  python3 checkpoint_gen.py resume <task_id>")
        sys.exit(1)
    
    cmd = sys.argv[1]
    task_id = sys.argv[2]
    
    if cmd == "gen-task-init":
        generate_task_init_checkpoint(task_id)
    elif cmd == "gen-structure":
        generate_structure_checkpoint(task_id)
    elif cmd == "gen-draft":
        scene_id = sys.argv[3] if len(sys.argv) > 3 else "chapter_1"
        word_count = int(sys.argv[4]) if len(sys.argv) > 4 else 0
        generate_draft_progress_checkpoint(task_id, scene_id, [], word_count)
    elif cmd == "resume":
        resume_from_checkpoint(task_id)
    else:
        print(f"Unknown command: {cmd}")