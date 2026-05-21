"""Chat router — Hermes Agent conversation panel embedded in Control Center.

Source=chat-panel to distinguish from Phase 5 command tasks.
Reuses existing tasks + task_messages tables.
"""
import subprocess
import json
import re
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc
from app.database import get_sync_session
from app.models.task import Task, TaskMessage

router = APIRouter(tags=["Chat"])


# ── Schemas ──


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: int
    tokens_used: Optional[int] = None


class ChatSessionItem(BaseModel):
    id: int
    title: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    message_count: int = 0

    class Config:
        from_attributes = True


# ── Endpoints ──


@router.post("/api/v1/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Send a message to Hermes Agent and stream back the reply.

    Creates a new session (if no session_id) or appends to an existing one.
    Calls ``hermes chat -q <message>`` in subprocess, parses stdout as reply.
    """
    db = get_sync_session()
    try:
        # ── Find or create session ──
        if req.session_id:
            task = (
                db.query(Task)
                .filter(Task.id == req.session_id, Task.source == "chat-panel")
                .first()
            )
            if not task:
                raise HTTPException(404, "Chat session not found")
        else:
            task = Task(
                title=req.message[:80],
                source="chat-panel",
                status="in_progress",
                agent_id="hermes",
            )
            db.add(task)
            db.commit()
            db.refresh(task)

        session_id = task.id

        # ── Save user message ──
        user_msg = TaskMessage(
            task_id=session_id,
            role="user",
            content=req.message,
        )
        db.add(user_msg)
        db.commit()

        # ── Call Hermes CLI ──
        try:
            result = subprocess.run(
                ["hermes", "chat", "-q", req.message, "--timeout", "180"],
                capture_output=True,
                text=True,
                timeout=185,
            )
            reply = (result.stdout or "").strip()
            if not reply:
                reply = (result.stderr or "").strip() or "(Hermes returned no output)"

            # Attempt to extract token count from stderr
            tokens: Optional[int] = None
            token_match = re.search(
                r"(\d+)\s*(?:tokens?|input|output)", (result.stdout or "") + (result.stderr or ""), re.IGNORECASE
            )
            if token_match:
                tokens = int(token_match.group(1))

        except subprocess.TimeoutExpired:
            reply = "⏱️ 请求超时（>3分钟），请重试或简化问题。"
            tokens = None
        except FileNotFoundError:
            reply = "❌ Hermes CLI 未安装。请运行 `pip install hermes-agent`。"
            tokens = None
        except Exception as e:
            reply = f"❌ 调用 Hermes 出错：{str(e)}"
            tokens = None

        # ── Save assistant reply ──
        metadata = json.dumps({"tokens_used": tokens}) if tokens is not None else None
        assistant_msg = TaskMessage(
            task_id=session_id,
            role="assistant",
            content=reply,
            msg_metadata=metadata,
        )
        db.add(assistant_msg)

        # ── Update task status ──
        task.status = "completed"
        task.result_summary = reply[:200] + ("..." if len(reply) > 200 else "")
        if tokens is not None:
            # Rough estimate: $2/M input tokens for DeepSeek V4
            task.cost_usd = round(tokens * 0.000002, 6)
        db.commit()

        return ChatResponse(
            reply=reply, session_id=session_id, tokens_used=tokens
        )

    finally:
        db.close()


@router.get("/api/v1/chat/sessions", response_model=List[ChatSessionItem])
def list_sessions(limit: int = Query(50, ge=1, le=200)):
    """List all non-archived chat sessions, newest first."""
    db = get_sync_session()
    try:
        tasks = (
            db.query(Task)
            .filter(Task.source == "chat-panel", Task.status != "archived")
            .order_by(desc(Task.updated_at))
            .limit(limit)
            .all()
        )
        result: List[ChatSessionItem] = []
        for t in tasks:
            msg_count = (
                db.query(TaskMessage)
                .filter(TaskMessage.task_id == t.id)
                .count()
            )
            result.append(
                ChatSessionItem(
                    id=t.id,
                    title=t.title,
                    status=t.status,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                    message_count=msg_count,
                )
            )
        return result
    finally:
        db.close()


@router.get("/api/v1/chat/sessions/{session_id}")
def get_session(session_id: int):
    """Get a chat session with its full message timeline."""
    db = get_sync_session()
    try:
        task = (
            db.query(Task)
            .filter(Task.id == session_id, Task.source == "chat-panel")
            .first()
        )
        if not task:
            raise HTTPException(404, "Chat session not found")

        messages = (
            db.query(TaskMessage)
            .filter(TaskMessage.task_id == session_id)
            .order_by(TaskMessage.created_at)
            .all()
        )

        return {
            "session": {
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
            },
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "metadata": m.msg_metadata,
                    "created_at": m.created_at,
                }
                for m in messages
            ],
        }
    finally:
        db.close()


@router.delete("/api/v1/chat/sessions/{session_id}")
def delete_session(session_id: int):
    """Soft-delete a chat session (archives it)."""
    db = get_sync_session()
    try:
        task = (
            db.query(Task)
            .filter(Task.id == session_id, Task.source == "chat-panel")
            .first()
        )
        if not task:
            raise HTTPException(404, "Chat session not found")
        task.status = "archived"
        db.commit()
        return {"status": "ok", "session_id": session_id}
    finally:
        db.close()
