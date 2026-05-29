# @PRODUCT Seed — v0.10 Skill Registry + Product Line Registry
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
    {"product_line_id": "ai-company-os", "name": "AI Company OS 自身", "description": "OS 平台能力建设", "owner_agent": "hermes", "status": "active", "related_skills": "research_agent,landing_page_copywriter,landing_page_builder"},
    {"product_line_id": "ai-seller-finance", "name": "AI经营系统 / 卖家财务", "description": "利润报告、财务分析", "owner_agent": "hermes", "status": "active", "related_skills": "profit_health_report_generator,research_agent,landing_page_copywriter"},
    {"product_line_id": "amazon-business", "name": "亚马逊跨境业务", "description": "运营、选品、供应链", "owner_agent": "hermes", "status": "active", "related_skills": "research_agent"},
    {"product_line_id": "digital-products", "name": "数字产品（电子书/课程/SaaS）", "description": "内容产品 + 独立站", "owner_agent": "hermes", "status": "active", "related_skills": "landing_page_copywriter,landing_page_builder,deployment_assistant"},
    {"product_line_id": "launch-sites", "name": "启动页 / 落地页", "description": "产品 landing page", "owner_agent": "hermes", "status": "active", "related_skills": "landing_page_copywriter,landing_page_builder,deployment_assistant"},
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
                    (product_line_id, name, description, owner_agent, status, related_skills)
                    VALUES (:product_line_id, :name, :description, :owner_agent, :status, :related_skills)"""),
                pl,
            )
        conn.commit()
    print(f"[seed_product_lines] Seeded {len(DEFAULT_PRODUCT_LINES)} default product lines (INSERT OR REPLACE)")
