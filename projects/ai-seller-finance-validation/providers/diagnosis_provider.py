"""
DiagnosisProvider — 异常诊断抽象接口

Usage:
    from providers.diagnosis_provider import DiagnosisProvider, DiagnosisResult
"""
from dataclasses import dataclass, field
from typing import Optional
from decimal import Decimal


@dataclass
class AbnormalItem:
    """单条异常记录"""
    metric: str
    actual: Decimal
    target: Decimal
    variance: Decimal
    variance_pct: float
    severity: str  # "low" | "medium" | "high" | "critical"
    root_cause: str = ""
    recommendation: str = ""
    affected_objects: list = field(default_factory=list)


@dataclass
class DiagnosisResult:
    """诊断结果"""
    summary: str
    key_findings: list
    abnormal_items: list
    recommendations: list
    risks: list = field(default_factory=list)


class DiagnosisProvider:
    """诊断提供者抽象接口"""

    def diagnose(self, period_data: dict, target_data: dict = None) -> DiagnosisResult:
        """分析经营数据，返回诊断结果"""
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self.__class__.__name__
