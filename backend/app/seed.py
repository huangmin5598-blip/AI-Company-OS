"""Mock data seed for v0.1 development."""
import json
from datetime import datetime, timedelta
from app.database import get_sync_session, init_db
from app.models.agent import Agent
from app.models.business_line import BusinessLine
from app.models.cron_job import CronJob
from app.models.execution_record import ExecutionRecord
from app.models.artifact import Artifact
from app.models.cost_snapshot import CostSnapshot
from app.models.alert import Alert

def now():
    return datetime.utcnow().isoformat() + "Z"

def seed_database():
    init_db()
    session = get_sync_session()

    # Check if already seeded
    if session.query(Agent).count() > 0:
        session.close()
        return

    # ── Agents ──
    agents_data = [
        ("main", "主 Agent", "~/.openclaw/workspace", True),
        ("tiger-coder", "😎 编程专家", "~/.openclaw/workspace-tiger-coder", False),
        ("amazon-seller", "🛒 亚马逊卖家专家", "~/.openclaw/workspace-amazon-seller", False),
        ("content-manager", "📱 自媒体运营专家", "~/.openclaw/workspace-content-manager", False),
        ("finance-analyst", "📊 金融分析师", "~/.openclaw/workspace-finance-analyst", False),
        ("course-builder", "📚 课程构建师", "~/.openclaw/workspace-course-builder", False),
        ("lead-hub", "🏗️ 独立站项目主管", "~/.openclaw/workspace-lead-hub", False),
        ("lead-sticker", "🎨 表情包项目主管", "~/.openclaw/workspace-lead-sticker", False),
        ("research-agent", "🔭 机会侦察兵", "~/.openclaw/workspace-research-agent", False),
        ("lead-novel", "📖 小说项目主管", "~/.openclaw/workspace-lead-novel", False),
        ("lead-motionclean", "🎬 项目主管", "~/.openclaw/workspace-lead-motionclean", False),
        ("story-editor", "✍️ 小说编辑", "~/.openclaw/workspace-story-editor", False),
        ("writer", "🖊️ 小说写手", "~/.openclaw/workspace-writer", False),
        ("review-editor", "🔎 审核编辑", "~/.openclaw/workspace-review-editor", False),
        ("lead-os", "🏗️ OS能力建设项目负责人", "~/.openclaw/workspace-lead-os", False),
    ]
    for name, ident, ws, is_def in agents_data:
        session.add(Agent(
            id=name, name=name, identity=ident, workspace=ws,
            model="MiniMax-M2.5", is_default=1 if is_def else 0,
            status="online", total_cost_usd=0.0,
            agent_type="openclaw",
            last_active_at=now(), created_at=now(), updated_at=now(),
        ))

    # ── Business Lines ──
    lines = [
        ("novel-v1", "小说日更", "guaranteed", '["lead-novel","story-editor","writer","review-editor"]',
         '["08:00 (1-6)","22:00 (1-6)"]', 28, 2, 0.00167, "2026-04-28", "passed"),
        ("content-manager", "内容运营", "running", '["content-manager"]',
         '["08:00","11:30","15:00"]', 42, 1, 0.0012, "2026-04-08", "passed"),
        ("finance-analyst", "金融分析", "running", '["finance-analyst"]',
         '["08:30 (1-5)","09:40 (1-5)","11:15 (1-5)","14:45 (1-5)"]', 60, 3, 0.0020, "2026-04-08", "passed"),
        ("amazon-seller", "亚马逊选品", "error", '["amazon-seller"]',
         '["15:00 Tue","09:00 Fri"]', 12, 4, 0.0008, "2026-04-25", "failed"),
        ("research-opportunity", "机会研究", "scaffolded", '["research-agent"]',
         '["09:00 Mon"]', 3, 0, 0.0005, "2026-04-06", "passed"),
    ]
    for lid, lname, status, agents, triggers, truns, fruns, cost, last_run, last_res in lines:
        session.add(BusinessLine(
            id=lid, name=lname, status=status,
            agent_ids=agents, triggers=triggers,
            total_runs=truns, failed_runs=fruns, total_cost_usd=cost,
            last_run_date=last_run, last_run_result=last_res,
            created_at=now(), updated_at=now(),
        ))

    # ── Cron Jobs ──
    cron_defs = [
        # novel-v1 (4)
        ("novel-primary-001", "小说日更-主生产", "main", "novel-v1", "0 8 * * 1-6", True, "ok"),
        ("novel-guarantee-001", "小说日更-保障检查", "main", "novel-v1", "0 22 * * 1-6", True, "ok"),
        ("novel-guarantee-run-001", "小说日更-保障补跑", "writer", "novel-v1", "30 22 * * 1-6", True, "ok"),
        ("novel-task-card-001", "小说日更-任务卡生成", "lead-novel", "novel-v1", "0 7 * * 1-6", True, "ok"),
        # content-manager (3)
        ("content-am-001", "小红书早间选题", "content-manager", "content-manager", "0 8 * * 1-5", True, "ok"),
        ("content-noon-001", "AI资讯摘要", "content-manager", "content-manager", "30 11 * * 1-5", True, "ok"),
        ("content-pm-001", "小红书下午选题", "content-manager", "content-manager", "0 15 * * 1-5", True, "ok"),
        # finance-analyst (5)
        ("finance-morning-001", "金融摘要-早间", "finance-analyst", "finance-analyst", "30 8 * * 1-5", True, "ok"),
        ("finance-am-001", "A股早盘", "finance-analyst", "finance-analyst", "40 9 * * 1-5", True, "ok"),
        ("finance-noon-001", "A股午盘", "finance-analyst", "finance-analyst", "15 11 * * 1-5", True, "ok"),
        ("finance-pm-001", "A股尾盘", "finance-analyst", "finance-analyst", "45 14 * * 1-5", True, "ok"),
        ("finance-weekend-001", "外围市场-周末", "finance-analyst", "finance-analyst", "0 20 * * 0,6", True, "error"),
        # amazon-seller (2)
        ("amazon-tue-001", "亚马逊选品-周二", "main", "amazon-seller", "0 15 * * 2", True, "ok"),
        ("amazon-fri-001", "亚马逊选品-周五", "main", "amazon-seller", "0 9 * * 5", True, "error"),
        # research (1)
        ("research-mon-001", "机会研究-周一", "research-agent", "research-opportunity", "0 9 * * 1", True, "ok"),
        # system (4)
        ("sys-report-001", "日报-18:00", "main", "", "0 18 * * *", True, "ok"),
        ("sys-heartbeat-001", "心跳检查-09:00", "main", "", "0 9 * * *", True, "ok"),
        ("sys-gateway-001", "Gateway健康检查", "main", "", "0 */12 * * *", True, "ok"),
        ("sys-weekly-001", "产品周报-周一", "main", "", "0 9 * * 1", True, "ok"),
        ("sys-research-weekly", "研究周报-周一", "research-agent", "", "0 9 * * 1", True, "ok"),
    ]
    for cid, cname, caid, blid, expr, enabled, status in cron_defs:
        err = None
        consec = 0
        if status == "error":
            consec = 3
            err = "cron announce delivery failed" if "weekend" in cid or "fri" in cid else "API request timeout"
        session.add(CronJob(
            id=cid, name=cname, agent_id=caid, business_line_id=blid,
            schedule_expr=expr, enabled=1 if enabled else 0,
            last_status=status, consecutive_errors=consec, last_error=err,
            last_run_at="2026-04-28T08:00:00Z",
            created_at=now(), updated_at=now(),
            data_source='mock',
            source_name='seed',
            source_path='',
            sync_batch_id='seed',
            last_synced_at=now(),
        ))

    # ── Execution Records ──
    execs = [
        ("rec-novel-44", "2026-04-28", "novel-v1", "novel-44", "第44章「暗流涌动」", 5063, "passed", 0.0004),
        ("rec-novel-111", "2026-04-26", "novel-v1", "guarantee-2026-04-26", "第111章（保障触发）", 6145, "passed", 0.0004),
        ("rec-novel-103", "2026-04-23", "novel-v1", "novel-42", "第103章", 2168, "passed", 0.0004),
        ("rec-novel-102", "2026-04-22", "novel-v1", "novel-41", "第102章", 580, "passed", 0.0004),
        ("rec-novel-37", "2026-04-15", "novel-v1", "novel-37", "Novel-37", 1900, "passed", 0.0004),
        ("rec-novel-36", "2026-04-12", "novel-v1", "novel-36", "Novel-36", 5101, "passed", 0.0004),
        ("rec-novel-35", "2026-04-11", "novel-v1", "novel-35", "Novel-35", 0, "failed", 0.0),
        ("rec-finance-0428-1", "2026-04-28", "finance-analyst", "fin-0428-m", "金融摘要-早间", 0, "passed", 0.00038),
        ("rec-finance-0428-2", "2026-04-28", "finance-analyst", "fin-0428-am", "A股早盘", 0, "passed", 0.00035),
        ("rec-finance-0428-3", "2026-04-28", "finance-analyst", "fin-0428-noon", "A股午盘", 0, "passed", 0.00032),
        ("rec-finance-0428-4", "2026-04-28", "finance-analyst", "fin-0428-pm", "A股尾盘", 0, "passed", 0.00030),
        ("rec-content-0428-1", "2026-04-28", "content-manager", "ctx-0428-am", "小红书选题-早间", 0, "passed", 0.00025),
        ("rec-content-0428-2", "2026-04-28", "content-manager", "ctx-0428-noon", "AI资讯摘要", 0, "passed", 0.00030),
        ("rec-content-0428-3", "2026-04-28", "content-manager", "ctx-0428-pm", "小红书选题-下午", 0, "passed", 0.00028),
        ("rec-amazon-tue-0425", "2026-04-25", "amazon-seller", "amz-tue-0425", "亚马逊选品-周二", 0, "passed", 0.00040),
        ("rec-amazon-fri-0425", "2026-04-25", "amazon-seller", "amz-fri-0425", "亚马逊选品-周五", 0, "failed", 0.0),
    ]
    for eid, date, bl, tid, title, wc, result, cost in execs:
        session.add(ExecutionRecord(
            id=eid, date=date, business_line=bl, task_id=tid, title=title,
            word_count=wc, result=result, cost_usd=cost, model="MiniMax-M2.5",
            created_at=now(),
            result_detail="AxiosError 400" if result == "failed" else None,
            data_source='mock',
            source_name='seed',
            source_path='',
            sync_batch_id='seed',
            last_synced_at=now(),
        ))

    # ── Artifacts ──
    artifacts = [
        ("art-novel-44", "rec-novel-44", "novel-v1", "2026-04-28",
         "manuscripts/2026-04-28/chapter-novel-44-2026-04-28.md", 5063, 10240, "md", 1, "validated"),
        ("art-novel-111", "rec-novel-111", "novel-v1", "2026-04-26",
         "manuscripts/2026-04-26/chapter-novel-111-2026-04-26.md", 6145, 12400, "md", 1, "delivered"),
        ("art-novel-103", "rec-novel-103", "novel-v1", "2026-04-23",
         "manuscripts/2026-04-23/chapter-novel-103-2026-04-23.md", 2168, 4800, "md", 1, "delivered"),
        ("art-novel-102", "rec-novel-102", "novel-v1", "2026-04-22",
         "manuscripts/2026-04-22/chapter-novel-102-2026-04-22.md", 580, 1400, "md", 1, "delivered"),
        ("art-novel-36", "rec-novel-36", "novel-v1", "2026-04-12",
         "manuscripts/2026-04-12/chapter-novel-36-2026-04-12.md", 5101, 10200, "md", 1, "delivered"),
    ]
    for aid, rid, bl, date, path, wc, size, ftype, vp, status in artifacts:
        session.add(Artifact(
            id=aid, run_id=rid, business_line=bl, date=date,
            artifact_path=path, word_count=wc, file_size_bytes=size,
            file_type=ftype, validator_passed=vp, artifact_status=status,
            cost_usd=0.0004, model="MiniMax-M2.5", created_at=now(),
            data_source='mock',
            source_name='seed',
            source_path='',
            sync_batch_id='seed',
            last_synced_at=now(),
        ))

    # ── Cost Snapshots (7 days) ──
    base_date = datetime(2026, 3, 30)
    agents_cost = ["finance-analyst", "research-agent", "lead-novel", "story-editor", "writer", "review-editor"]
    models_cost = [("MiniMax-M2.5", 0.00038), ("deepseek-r1:8b", 0.0)]
    for day in range(7):
        d = (base_date + timedelta(days=day)).strftime("%Y-%m-%d")
        for i, agent in enumerate(agents_cost):
            model, cost_per_call = models_cost[i % 2]
            session.add(CostSnapshot(
                date=d, agent_id=agent, model=model, provider="minimax-cn",
                input_tokens=80 + i * 20, output_tokens=100 + i * 30,
                cost_usd=cost_per_call, result_status="success",
                task_hint=f"Mock task for {agent} on {d}",
                created_at=now(),
                data_source='mock',
                source_name='seed',
                source_path='',
                sync_batch_id='seed',
                last_synced_at=now(),
            ))

    # ── Alerts ──
    session.add(Alert(
        severity="error", title="亚马逊选品报告连续失败",
        description="周五触发报告时持续 AxiosError 400，已连续报错 3 次，需要检查 API 密钥和网络连接。",
        source="cron:amazon-seller", source_id="amazon-fri-001",
        resolved=0, created_at=now(),
        data_source='mock',
        source_name='seed',
        source_path='',
        sync_batch_id='seed',
        last_synced_at=now(),
    ))
    session.add(Alert(
        severity="warning", title="外围市场动态消息发送失败",
        description="周末外围市场动态连续报错，消息推送失败，需要检查飞书 webhook 配置。",
        source="cron:finance-analyst", source_id="finance-weekend-001",
        resolved=0, created_at=now(),
        data_source='mock',
        source_name='seed',
        source_path='',
        sync_batch_id='seed',
        last_synced_at=now(),
    ))

    session.commit()
    counts = {
        "agents": session.query(Agent).count(),
        "business_lines": session.query(BusinessLine).count(),
        "cron_jobs": session.query(CronJob).count(),
        "execution_records": session.query(ExecutionRecord).count(),
        "artifacts": session.query(Artifact).count(),
        "cost_snapshots": session.query(CostSnapshot).count(),
        "alerts": session.query(Alert).count(),
    }
    session.close()
    return counts


def clear_and_reseed():
    """Drop all data and re-seed. Used by Refresh API."""
    from app.database import sync_engine
    from app.models.base import Base
    Base.metadata.drop_all(bind=sync_engine)
    return seed_database()
