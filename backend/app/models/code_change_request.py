# @PRODUCT Model — v0.9 Code-Capable Runtime Bridge
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class CodeChangeRequest(Base):
    __tablename__ = "code_change_requests"

    id = Column(Integer, primary_key=True)
    source_type = Column(String, nullable=False)
    # improvement_proposal / goal / manual
    source_id = Column(String, nullable=True)
    execution_request_id = Column(Integer, nullable=False)
    # 关联 execution_requests
    runtime_id = Column(String, nullable=True)
    # codex / claude_code
    title = Column(String, nullable=False)
    # 用户可理解的标题
    problem_summary = Column(Text, nullable=True)
    # 要解决的问题
    plan_summary = Column(Text, nullable=True)
    # Coding Agent 生成的自然语言方案
    impact_scope = Column(Text, nullable=True)
    # 影响范围描述
    risk_level = Column(String, nullable=False, default="medium")
    # low / medium / high
    files_expected_json = Column(Text, nullable=True)
    # JSON: 预计修改的文件列表 (用于 pre-check)
    files_changed_json = Column(Text, nullable=True)
    # JSON: 实际修改的文件列表 (用于 post-check)
    patch_diff = Column(Text, nullable=True)
    # git diff 格式 patch 文本
    diff_summary = Column(Text, nullable=True)
    # 自然语言 diff 摘要
    check_result_json = Column(Text, nullable=True)
    # JSON: 自动检查结果
    protected_file_check_json = Column(Text, nullable=True)
    # JSON: { pre_check, post_check }
    applied_with_warning = Column(Integer, default=0)
    # checks_warning 时 apply 的记录标志
    status = Column(String, nullable=False, default="draft")
    # draft → plan_generated → plan_approved → patch_generated
    # → checks_running → checks_passed / checks_warning / checks_failed
    # → founder_review → applied / rolled_back / rejected
    plan_approved_by = Column(String, nullable=True)
    plan_approved_at = Column(DateTime, nullable=True)
    applied_by = Column(String, nullable=True)
    applied_at = Column(DateTime, nullable=True)
    rolled_back_by = Column(String, nullable=True)
    rolled_back_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
