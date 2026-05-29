# @PRODUCT Seed — v0.12 Skill Registry + Product Line Registry (Agent Boundaries)
from app.database import sync_engine
from sqlalchemy import text

DEFAULT_SKILLS = [
    {
        "skill_id": "research_agent",
        "name": "Research Agent",
        "description": "市场/用户研究、痛点分析、竞品扫描",
        "capability_type": "research",
        "owner_agent": "hermes",
        "owner_runtime": "hermes",
        "risk_level": "low",
        "execution_mode": "direct_delegate",
        "examples": "整理目标用户痛点和卖点",
        "status": "active",
    },
    {
        "skill_id": "landing_page_copywriter",
        "name": "Landing Page Copywriter",
        "description": "生成产品落地页文案",
        "capability_type": "copywriting",
        "owner_agent": "hermes",
        "owner_runtime": "hermes",
        "risk_level": "low",
        "execution_mode": "direct_delegate",
        "examples": "为利润报告准备销售页文案",
        "status": "active",
    },
    {
        "skill_id": "landing_page_builder",
        "name": "Landing Page Builder",
        "description": "生成静态落地页代码",
        "capability_type": "code_build",
        "owner_agent": "codex",
        "owner_runtime": "codex",
        "risk_level": "medium",
        "execution_mode": "code_bridge",
        "examples": "生成利润报告销售页 Next.js 页面",
        "status": "active",
    },
    {
        "skill_id": "deployment_assistant",
        "name": "Deployment Assistant",
        "description": "生成部署 checklist，不自动执行 shell",
        "capability_type": "deploy",
        "owner_agent": "codex",
        "owner_runtime": "shell",
        "risk_level": "high",
        "execution_mode": "checklist_only",
        "examples": "Cloudflare Pages / GitHub Pages 部署说明",
        "status": "active",
    },
    {
        "skill_id": "profit_health_report_generator",
        "name": "Profit Health Report Generator",
        "description": "Amazon 利润体检报告生成器（本地脚本）",
        "capability_type": "report_generation",
        "owner_agent": "local",
        "owner_runtime": "local",
        "risk_level": "low",
        "execution_mode": "local_script",
        "examples": "从 CSV 生成利润体检报告",
        "status": "active",
    },
]

DEFAULT_PRODUCT_LINES = [
    {
        "product_line_id": "ai-company-os",
        "name": "AI Company OS 自身",
        "description": "OS 平台能力建设：架构、版本、Skill 体系、发布管理",
        "owner_agent": "hermes (CEO)",
        "status": "active",
        "related_skills": "research_agent,landing_page_copywriter,landing_page_builder,deployment_assistant",
        "scope": "OS 体系架构设计、版本路线图、核心服务开发、公开证据层维护、商业化策略",
        "current_goal": "v0.12 Product Line Agents MVP — 建立产品线 Agent 责任体系和产品线状态汇总能力",
        "active_projects": '["v0.12 Product Line Agents MVP", "Launch Pipeline v0.11 维护", "Open Core 策略落地"]',
        "weekly_status": "v0.11 上线完成（Launch Pipeline），进入 v0.12 产品线 Agent 体系构建。GitHub 已标记 v0.10+v0.11。NOTICE.md 发布确认 All Rights Reserved。",
    },
    {
        "product_line_id": "ai-seller-finance",
        "name": "AI经营系统 / 卖家财务",
        "description": "利润报告、财务分析、AI经营系统平台",
        "owner_agent": "hermes",
        "status": "active",
        "related_skills": "profit_health_report_generator,research_agent,landing_page_copywriter,landing_page_builder",
        "scope": "Amazon 卖家财务产品设计、利润报告生成器迭代、AI经营系统（aifinance.ai-company-os.com）运营",
        "current_goal": "利润体检报告体验官招募准备 + Web 化（当前为本地脚本）",
        "active_projects": '["利润体检报告 MVP", "AI经营系统 Web 运营"]',
        "weekly_status": "销售页已部署 profit.ai-company-os.com（SSL 签发中）。产品仍为本地脚本，需 Web 化。体验官招募待启动。",
    },
    {
        "product_line_id": "amazon-business",
        "name": "亚马逊跨境业务",
        "description": "运营、选品、供应链、利润管理",
        "owner_agent": "hermes",
        "status": "active",
        "related_skills": "research_agent,profit_health_report_generator",
        "scope": "亚马逊店铺自有运营管理、选品分析、供应链优化、利润监控",
        "current_goal": "暂无活跃目标 — 等待利润体检报告产品化后复用",
        "active_projects": '[]',
        "weekly_status": "当前无活跃开发项目。利润体检报告产品化后作为首个内部客户。",
    },
    {
        "product_line_id": "digital-products",
        "name": "数字产品",
        "description": "电子书、课程、SaaS、模板包、知识产品",
        "owner_agent": "hermes",
        "status": "incubating",
        "related_skills": "landing_page_copywriter,landing_page_builder,deployment_assistant,research_agent",
        "scope": "数字内容产品开发：电子书、在线课程、模板包、AI 工具、SaaS MVP",
        "current_goal": "AI Company OS Operating Kit 内容整理（LR-002）",
        "active_projects": '["AI Company OS Operating Kit (LR-002)"]',
        "weekly_status": "Operating Kit 的 launch package 已通过 Launch Pipeline 生成（LR-002）。内容整理尚未开始。定价待定。",
    },
    {
        "product_line_id": "launch-sites",
        "name": "启动页 / 落地页",
        "description": "产品 landing page、上线发布、SEO 基础",
        "owner_agent": "hermes",
        "status": "active",
        "related_skills": "landing_page_copywriter,landing_page_builder,deployment_assistant,research_agent",
        "scope": "产品 launch pipeline 运维、销售页生成与部署、上线流程持续优化",
        "current_goal": "Launch Pipeline 模板优化 — 支持更多页面类型和定价方案",
        "active_projects": '["Launch Pipeline v0.11 维护", "profit.ai-company-os.com 运营"]',
        "weekly_status": "Launch Pipeline v0.11 上线。支持服务和内容两种产品类型。profit.ai-company-os.com 已部署。",
    },
    {
        "product_line_id": "entertainment-products",
        "name": "娱乐产品",
        "description": "AI 短剧、AI 音乐、AI 小说、AI 游戏",
        "owner_agent": "hermes",
        "status": "incubating",
        "related_skills": "research_agent",
        "scope": "AI 生成内容产品探索：短剧脚本、音乐生成、互动小说、轻量游戏",
        "current_goal": "机会扫描 — 分析 AI 短剧/音乐/游戏的市场机会和最低验证路径",
        "active_projects": '["娱乐产品机会扫描"]',
        "weekly_status": "处于孵化期，尚未进入正式开发。计划进行市场机会扫描后决定首个验证项目。",
    },
]


def seed_skills():
    """Insert or update default skills. Idempotent — safe to call on every startup."""
    with sync_engine.connect() as conn:
        for s in DEFAULT_SKILLS:
            conn.execute(
                text("""INSERT OR REPLACE INTO skill_registry
                    (skill_id, name, description, capability_type, owner_agent,
                     owner_runtime, risk_level, execution_mode, examples, status)
                    VALUES (:skill_id, :name, :description, :capability_type, :owner_agent,
                            :owner_runtime, :risk_level, :execution_mode, :examples, :status)"""),
                s,
            )
        conn.commit()
    print(f"[seed_skills] Seeded {len(DEFAULT_SKILLS)} default skills (INSERT OR REPLACE)")


def seed_product_lines():
    """Insert or update default product lines. Idempotent."""
    with sync_engine.connect() as conn:
        for pl in DEFAULT_PRODUCT_LINES:
            conn.execute(
                text("""INSERT OR REPLACE INTO product_line_registry
                    (product_line_id, name, description, owner_agent, status,
                     related_skills, scope, current_goal, active_projects, weekly_status)
                    VALUES (:product_line_id, :name, :description, :owner_agent, :status,
                            :related_skills, :scope, :current_goal, :active_projects, :weekly_status)"""),
                pl,
            )
        conn.commit()
    print(f"[seed_product_lines] Seeded {len(DEFAULT_PRODUCT_LINES)} default product lines (INSERT OR REPLACE)")
