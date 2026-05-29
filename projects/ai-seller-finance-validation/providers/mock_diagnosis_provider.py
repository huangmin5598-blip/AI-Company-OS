"""
MockDiagnosisProvider — 规则版异常诊断

基于实际 vs 目标的偏差计算，返回诊断结果。
不依赖 LLM，所有逻辑在 Python 中完成。

当冷启动有付费信号后，替换为 LLM 版：
    FutureLLMDiagnosisProvider(DiagnosisProvider)
"""
from decimal import Decimal
from providers.diagnosis_provider import DiagnosisProvider, DiagnosisResult, AbnormalItem


class MockDiagnosisProvider(DiagnosisProvider):
    """规则驱动的诊断提供者（暂代 LLM，不阻塞）"""

    def __init__(self):
        self._name = "mock-diagnosis-provider"

    @property
    def name(self) -> str:
        return self._name

    def diagnose(self, period_data: dict, target_data: dict = None) -> DiagnosisResult:
        """根据实际数据 vs 目标数据，计算异常项"""
        abnormal_items = []

        # 需要检查的指标
        checks = [
            ("net_profit", "净利润"),
            ("ad_spend_rate", "广告费占比"),
            ("net_profit_margin", "净利润率"),
            ("return_rate", "退款率"),
        ]

        for key, label in checks:
            actual = period_data.get(key, 0)
            target = target_data.get(key) if target_data else None

            if target is None or target == 0:
                continue

            if isinstance(actual, Decimal):
                actual_f = float(actual)
            else:
                actual_f = float(actual)

            if isinstance(target, Decimal):
                target_f = float(target)
            else:
                target_f = float(target)

            variance = actual_f - target_f
            if target_f != 0:
                variance_pct = round((variance / target_f) * 100, 1)
            else:
                variance_pct = 0.0

            # 判断严重程度
            severity = self._judge_severity(key, variance_pct)

            if severity == "normal":
                continue

            root_cause, recommendation = self._get_diagnosis(key, actual_f, target_f, variance, variance_pct)

            abnormal_items.append(AbnormalItem(
                metric=key,
                actual=Decimal(str(actual_f)),
                target=Decimal(str(target_f)),
                variance=Decimal(str(round(variance, 2))),
                variance_pct=variance_pct,
                severity=severity,
                root_cause=root_cause,
                recommendation=recommendation,
                affected_objects=period_data.get("affected_skus", []),
            ))

        # 生成 summary
        if abnormal_items:
            total_impact = sum(abs(item.variance) for item in abnormal_items if item.variance < 0)
            summary = f"本月存在 {len(abnormal_items)} 项异常，总影响金额约 ¥{float(total_impact):,.0f}"
        else:
            summary = "本月经营状况基本正常，无重大异常。"

        key_findings = []
        for item in abnormal_items:
            key_findings.append(item.root_cause)

        recommendations = []
        for item in abnormal_items:
            if item.recommendation:
                recommendations.append(item.recommendation)

        return DiagnosisResult(
            summary=summary,
            key_findings=key_findings,
            abnormal_items=abnormal_items,
            recommendations=recommendations,
            risks=[],
        )

    def _judge_severity(self, key: str, variance_pct: float) -> str:
        """根据指标类型和偏差幅度判断严重程度"""
        thresholds = {
            "net_profit": (-5, -15, -30),          # 负偏差
            "net_profit_margin": (-10, -25, -50),
            "ad_spend_rate": (5, 15, 30),           # 正偏差（费用超支）
            "return_rate": (1, 3, 5),               # 正偏差
        }

        low, medium, high = thresholds.get(key, (10, 20, 40))

        abs_vp = abs(variance_pct)
        if abs_vp <= abs(low):
            return "normal"
        elif abs_vp <= abs(medium):
            return "medium"
        elif abs_vp <= abs(high):
            return "high"
        else:
            return "critical"

    def _get_diagnosis(self, key: str, actual: float, target: float,
                       variance: float, variance_pct: float) -> tuple:
        """生成 root_cause 和 recommendation（规则版，LLM 版会替换此方法）"""

        diagnostics = {
            "net_profit": (
                f"净利润 ¥{actual:,.0f} 较目标 ¥{target:,.0f} 偏离 {variance_pct:+.1f}%，"
                f"差额 ¥{abs(variance):,.0f}。建议优先排查费用增长和毛利率变动。",
                "建议：1）分析费用增长原因；2）检查高毛利SKU的销量变化；3）评估广告ROI。"
            ),
            "ad_spend_rate": (
                f"广告费占比 {actual:.1f}%，较目标 {target:.1f}% 超支 {variance_pct:+.1f}%。"
                f"建议检查高ACOS广告活动。",
                "建议：1）暂停ACOS>30%的广告活动；2）优化关键词匹配方式；3）评估广告预算分配。"
            ),
            "net_profit_margin": (
                f"净利润率 {actual:.1f}% 较目标 {target:.1f}% 下降 {abs(variance_pct):.1f}%。"
                f"利润率下行需要关注。",
                "建议：1）分析成本结构变化；2）评估提价空间；3）排查低毛利SKU。"
            ),
            "return_rate": (
                f"退款率 {actual:.1f}% 较目标 {target:.1f}% 上升 {abs(variance_pct):.1f}%。"
                f"高退款率直接影响净利润。",
                "建议：1）检查近期差评和产品质量；2）核对Listing描述是否夸大；3）分析退款原因分布。"
            ),
        }

        return diagnostics.get(key, (f"{key} 偏离 {variance_pct:+.1f}%", "建议进一步分析。"))
