#!/usr/bin/env python3
"""
generate_profit_health_report.py — OP-006 Validation Build

Amazon 利润体检报告生成器。

用法：
    python scripts/generate_profit_health_report.py --sample
    python scripts/generate_profit_health_report.py --csv data.csv --output report.md
    python scripts/generate_profit_health_report.py --json data.json -o report.md

输出：Markdown 格式利润体检报告

时间盒：4-6 小时第一版
不依赖 AI经营系统 DB / API，独立运行。
"""
import argparse
import csv
import json
import os
import sys
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Optional

# ── 路径设置 ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from providers.diagnosis_provider import DiagnosisProvider, DiagnosisResult, AbnormalItem
from providers.mock_diagnosis_provider import MockDiagnosisProvider


# ═══════════════════════════════════════════
# 数据类型
# ═══════════════════════════════════════════

@dataclass
class SKUData:
    sku: str
    asin: str = ""
    units_sold: int = 0
    gross_sales: Decimal = Decimal("0")
    refunds: Decimal = Decimal("0")
    product_cost: Decimal = Decimal("0")
    ad_spend: Decimal = Decimal("0")
    fba_fee: Decimal = Decimal("0")
    referral_fee: Decimal = Decimal("0")
    contribution_profit: Decimal = Decimal("0")


@dataclass
class AdCampaignData:
    campaign_id: str
    campaign_name: str = ""
    spend: Decimal = Decimal("0")
    sales: Decimal = Decimal("0")
    impressions: int = 0
    clicks: int = 0


@dataclass
class ProfitHealthData:
    """利润体检输入数据"""
    period: str
    store: str = "Amazon"
    currency: str = "CNY"

    # 汇总指标
    total_sales: Decimal = Decimal("0")
    refunds: Decimal = Decimal("0")
    promotions: Decimal = Decimal("0")
    net_sales: Decimal = Decimal("0")
    product_cost: Decimal = Decimal("0")
    referral_fee: Decimal = Decimal("0")
    fba_fee: Decimal = Decimal("0")
    fba_storage: Decimal = Decimal("0")
    ad_spend: Decimal = Decimal("0")
    other_fees: Decimal = Decimal("0")
    gross_profit: Decimal = Decimal("0")
    net_profit: Decimal = Decimal("0")
    gross_margin: float = 0.0
    net_margin: float = 0.0
    ad_spend_rate: float = 0.0
    return_rate: float = 0.0
    tacos: float = 0.0

    # 明细
    skus: list = field(default_factory=list)
    ad_campaigns: list = field(default_factory=list)

    # 可选：目标数据
    target_sales: Optional[Decimal] = None
    target_profit: Optional[Decimal] = None
    target_ad_rate: Optional[Decimal] = None


# ═══════════════════════════════════════════
# 指标计算
# ═══════════════════════════════════════════

def compute_metrics(data: ProfitHealthData) -> ProfitHealthData:
    """从原始数据计算派生指标"""
    # 汇总计算
    data.net_sales = data.total_sales - data.refunds - data.promotions
    data.gross_profit = data.net_sales - data.product_cost
    total_fees = (data.referral_fee + data.fba_fee + data.fba_storage
                  + data.ad_spend + data.other_fees)
    data.net_profit = data.gross_profit - total_fees

    # 比率
    if data.net_sales > 0:
        data.gross_margin = round(float(data.gross_profit / data.net_sales * 100), 1)
        data.net_margin = round(float(data.net_profit / data.net_sales * 100), 1)
        data.ad_spend_rate = round(float(data.ad_spend / data.net_sales * 100), 1)
        data.return_rate = round(float(data.refunds / data.total_sales * 100), 1) if data.total_sales > 0 else 0.0
        data.tacos = round(float((data.ad_spend + data.refunds) / data.total_sales * 100), 1)

    return data


# ═══════════════════════════════════════════
# 报告生成器
# ═══════════════════════════════════════════

def generate_report(data: ProfitHealthData, diagnosis: DiagnosisResult, output_path: str = None) -> str:
    """生成 Markdown 格式的利润体检报告"""
    lines = []

    # ── 标题 ──
    lines.append(f"# Amazon 利润体检报告")
    lines.append(f"")
    lines.append(f"| 项目 | 内容 |")
    lines.append(f"|:-----|:-----|")
    lines.append(f"| 店铺 | {data.store} |")
    lines.append(f"| 期间 | {data.period} |")
    lines.append(f"| 生成时间 | {datetime.now().strftime('%Y-%m-%d %H:%M')} |")
    lines.append(f"| 币种 | {data.currency} |")
    lines.append(f"| 报告版本 | v0.1（验证版） |")
    lines.append(f"")

    # ── 1. 经营结论 ──
    profit_label = "🟢" if data.net_margin >= 10 else ("🟡" if data.net_margin >= 5 else "🔴")
    ad_label = "🟢" if data.ad_spend_rate <= 15 else ("🟡" if data.ad_spend_rate <= 25 else "🔴")
    return_label = "🟢" if data.return_rate <= 3 else ("🟡" if data.return_rate <= 7 else "🔴")

    lines.append(f"## 一、经营结论")
    lines.append(f"")
    lines.append(f"**诊断摘要：** {diagnosis.summary}")
    lines.append(f"")
    lines.append(f"| 指标 | 数值 | 评价 |")
    lines.append(f"|:-----|:-----|:-----|")
    lines.append(f"| 总销售额 | ¥{float(data.total_sales):,.0f} | — |")
    lines.append(f"| 净销售额 | ¥{float(data.net_sales):,.0f} | — |")
    lines.append(f"| 净利润 | ¥{float(data.net_profit):,.0f} | {profit_label} |")
    lines.append(f"| 净利润率 | {data.net_margin:.1f}% | {profit_label} |")
    lines.append(f"| 广告费占比 | {data.ad_spend_rate:.1f}% | {ad_label} |")
    lines.append(f"| 退款率 | {data.return_rate:.1f}% | {return_label} |")
    lines.append(f"")

    # ── 2. P&L 总览 ──
    lines.append(f"## 二、利润总览（P&L Summary）")
    lines.append(f"")
    lines.append(f"| 行项目 | 金额 | 占净销售额比 |")
    lines.append(f"|:------|:-----|:-----------|")
    lines.append(f"| **总销售额（Gross Sales）** | ¥{float(data.total_sales):,.0f} | 100% |")
    lines.append(f"| 退款（Refunds） | ¥{float(data.refunds):,.0f} | {data.return_rate:.1f}% |")
    lines.append(f"| 促销（Promotions） | ¥{float(data.promotions):,.0f} | — |")
    lines.append(f"| **净销售额（Net Sales）** | ¥{float(data.net_sales):,.0f} | 100% |")
    lines.append(f"| 产品成本 | ¥{float(data.product_cost):,.0f} | {_pct(data.product_cost, data.net_sales)} |")
    lines.append(f"| 平台佣金 | ¥{float(data.referral_fee):,.0f} | {_pct(data.referral_fee, data.net_sales)} |")
    lines.append(f"| FBA 配送费 | ¥{float(data.fba_fee):,.0f} | {_pct(data.fba_fee, data.net_sales)} |")
    lines.append(f"| FBA 仓储费 | ¥{float(data.fba_storage):,.0f} | {_pct(data.fba_storage, data.net_sales)} |")
    lines.append(f"| 广告费 | ¥{float(data.ad_spend):,.0f} | {_pct(data.ad_spend, data.net_sales)} |")
    lines.append(f"| 其他费用 | ¥{float(data.other_fees):,.0f} | {_pct(data.other_fees, data.net_sales)} |")
    lines.append(f"| **毛利（Gross Profit）** | ¥{float(data.gross_profit):,.0f} | {data.gross_margin:.1f}% |")
    lines.append(f"| **净利润（Contribution Profit）** | ¥{float(data.net_profit):,.0f} | **{data.net_margin:.1f}%** |")
    lines.append(f"")

    # ── 3. 费用分析 ──
    lines.append(f"## 三、费用分析")
    lines.append(f"")
    fee_rows = [
        ("平台佣金", data.referral_fee),
        ("FBA 配送费", data.fba_fee),
        ("FBA 仓储费", data.fba_storage),
        ("广告费", data.ad_spend),
        ("其他费用", data.other_fees),
    ]
    total_fees = sum(f[1] for f in fee_rows)
    lines.append(f"| 费用类型 | 金额 | 占总费用比 |")
    lines.append(f"|:---------|:-----|:---------|")
    for name, amount in fee_rows:
        pct = _pct(amount, total_fees)
        bar = _bar(float(amount), float(total_fees))
        lines.append(f"| {name} | ¥{float(amount):,.0f} | {pct} |")
    lines.append(f"| **费用总计** | **¥{float(total_fees):,.0f}** | **100%** |")
    lines.append(f"")

    # 费用结构图
    lines.append(f"**费用结构占比（估算）：**")
    lines.append(f"```")
    for name, amount in fee_rows:
        bar = _bar(float(amount), float(total_fees))
        pct = _pct(amount, total_fees)
        lines.append(f"{name:<10} {bar} {pct}")
    lines.append(f"```")
    lines.append(f"")

    # ── 4. 广告效率 ──
    lines.append(f"## 四、广告效率分析")
    lines.append(f"")
    total_ad_sales = sum(c.sales for c in data.ad_campaigns)
    acos = round(float(data.ad_spend / total_ad_sales * 100), 1) if total_ad_sales > 0 else 0
    acos_label = "🟢" if acos <= 15 else ("🟡" if acos <= 25 else "🔴")

    lines.append(f"| 指标 | 本月 | 评价 |")
    lines.append(f"|:-----|:-----|:-----|")
    lines.append(f"| 广告花费 | ¥{float(data.ad_spend):,.0f} | — |")
    lines.append(f"| 广告销售额 | ¥{float(total_ad_sales):,.0f} | — |")
    lines.append(f"| ACOS | {acos:.1f}% | {acos_label} |")
    lines.append(f"| 广告费占总收入比 | {data.ad_spend_rate:.1f}% | {ad_label} |")
    lines.append(f"| TACOS | {data.tacos:.1f}% | — |")
    lines.append(f"")

    # 各 campaign
    if data.ad_campaigns:
        lines.append(f"**各广告活动表现：**")
        lines.append(f"")
        lines.append(f"| Campaign | Spend | Sales | ACOS |")
        lines.append(f"|:---------|:------|:------|:-----|")
        for c in sorted(data.ad_campaigns, key=lambda x: x.spend, reverse=True):
            c_acos = round(float(c.spend / c.sales * 100), 1) if c.sales > 0 else 0
            c_label = "🟢" if c_acos <= 15 else ("🟡" if c_acos <= 25 else "🔴")
            lines.append(f"| {c.campaign_name or c.campaign_id} | ¥{float(c.spend):,.0f} | ¥{float(c.sales):,.0f} | {c_acos:.1f}% {c_label} |")
        lines.append(f"")

    # ── 5. 异常诊断 ──
    lines.append(f"## 五、异常诊断")
    lines.append(f"")
    if diagnosis.abnormal_items:
        lines.append(f"| # | 异常类型 | 描述 | 影响金额 | 严重程度 |")
        lines.append(f"|:-:|:---------|:-----|:---------|:---------|")
        for i, item in enumerate(diagnosis.abnormal_items, 1):
            sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(item.severity, "⚪")
            impact = f"¥{float(abs(item.variance)):,.0f}" if item.variance != 0 else "—"
            lines.append(f"| {i} | {item.metric} | {item.root_cause[:50]}... | {impact} | {sev_icon} {item.severity} |")
        lines.append(f"")
        # 详细说明
        for item in diagnosis.abnormal_items:
            lines.append(f"**{item.metric}：** {item.root_cause}")
            lines.append(f"")
            if item.recommendation:
                lines.append(f"> 💡 {item.recommendation}")
                lines.append(f"")
    else:
        lines.append(f"本月未发现重大异常。")
        lines.append(f"")

    # ── 6. 利润变化原因 ──
    lines.append(f"## 六、利润变化原因分析")
    lines.append(f"")
    lines.append(f"| 驱动因素 | 估算影响 | 说明 |")
    lines.append(f"|:---------|:---------|:-----|")
    # 基于诊断结果的简单分析
    if diagnosis.abnormal_items:
        for item in diagnosis.abnormal_items:
            lines.append(f"| {item.metric} | ¥{float(abs(item.variance)):,.0f} | {item.root_cause[:60]} |")
    else:
        lines.append(f"| — | — | 本月利润变化在正常范围 |")
    lines.append(f"")

    # ── 7. 经营建议 ──
    lines.append(f"## 七、经营建议")
    lines.append(f"")
    if diagnosis.recommendations:
        for i, rec in enumerate(diagnosis.recommendations, 1):
            lines.append(f"{i}. {rec}")
            lines.append(f"")
    else:
        lines.append(f"- 本月经营状态健康，建议维持当前策略。")
        lines.append(f"")

    # ── 8. 需补充数据 ──
    lines.append(f"## 八、需要补充的数据")
    lines.append(f"")
    lines.append(f"以下数据有助于更深入的分析：")
    lines.append(f"")
    lines.append(f"| 数据项 | 用途 | 优先级 |")
    lines.append(f"|:-------|:-----|:-------|")
    lines.append(f"| 广告活动报告（Sponsored Products） | 详细分析广告效率 | P1 |")
    lines.append(f"| 退货报告（Returns Report） | 分析退款原因 | P1 |")
    lines.append(f"| 库存报告 | 分析仓储成本和周转 | P2 |")
    lines.append(f"| 采购成本明细 | 精确计算 COGS | P2 |")
    lines.append(f"")

    # ── 9. 免责声明 ──
    lines.append(f"## 九、免责声明")
    lines.append(f"")
    lines.append(f"> ⚠️ **本报告为经营分析工具，不构成财务审计、税务建议或法律意见。**")
    lines.append(f">")
    lines.append(f"> - 数据来源：您提供的 Amazon Settlement Report / 经营数据")
    lines.append(f"> - 分析方式：规则驱动 + AI 辅助分析（验证版使用 Mock 诊断）")
    lines.append(f"> - 报告准确性取决于原始数据的完整性和准确性")
    lines.append(f"> - 建议人工复核关键数据后再做经营决策")
    lines.append(f"> - 本报告为验证版，后续版本将接入真实 AI 分析")
    lines.append(f"")

    # ── 页脚 ──
    lines.append(f"---")
    lines.append(f"*报告 ID：{uuid.uuid4().hex[:12]}*")
    lines.append(f"*生成工具：OP-006 Validation Build v0.1*")
    lines.append(f"*Powered by Hermes Agent + AI经营系统*")
    lines.append(f"")

    report_text = "\n".join(lines)

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_text)
        print(f"✅ 报告已保存：{output_path}")

    return report_text


# ═══════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════

def _pct(part, total) -> str:
    if total == 0:
        return "—"
    return f"{float(part) / float(total) * 100:.1f}%"


def _bar(value: float, total: float, width=20) -> str:
    if total == 0:
        return "—"
    ratio = value / total
    filled = max(1, int(ratio * width))
    return "█" * filled + "░" * (width - filled)


# ═══════════════════════════════════════════
# 数据加载
# ═══════════════════════════════════════════

def load_sample_data() -> ProfitHealthData:
    """内置样例数据（基于 Mock Settlement Report 结构）"""
    data = ProfitHealthData(
        period="2026年5月",
        total_sales=Decimal("1024680"),
        refunds=Decimal("36200"),
        promotions=Decimal("8500"),
        product_cost=Decimal("512340"),
        referral_fee=Decimal("102468"),
        fba_fee=Decimal("81974"),
        fba_storage=Decimal("15370"),
        ad_spend=Decimal("187500"),
        other_fees=Decimal("5100"),
        target_profit=Decimal("120000"),  # 目标净利润
        target_ad_rate=Decimal("15"),     # 目标广告占比
        skus=[
            SKUData(sku="SKU-A", asin="B0XXX", units_sold=1520, gross_sales=Decimal("456000"),
                    refunds=Decimal("9120"), product_cost=Decimal("228000"), ad_spend=Decimal("68400"),
                    fba_fee=Decimal("36480"), referral_fee=Decimal("45600"), contribution_profit=Decimal("68400")),
            SKUData(sku="SKU-B", asin="B0YYY", units_sold=890, gross_sales=Decimal("311500"),
                    refunds=Decimal("15575"), product_cost=Decimal("155750"), ad_spend=Decimal("62300"),
                    fba_fee=Decimal("24920"), referral_fee=Decimal("31150"), contribution_profit=Decimal("21805")),
            SKUData(sku="SKU-C", asin="B0ZZZ", units_sold=430, gross_sales=Decimal("172000"),
                    refunds=Decimal("8600"), product_cost=Decimal("103200"), ad_spend=Decimal("34400"),
                    fba_fee=Decimal("13760"), referral_fee=Decimal("17200"), contribution_profit=Decimal("-5160")),
            SKUData(sku="SKU-D", asin="B0WWW", units_sold=680, gross_sales=Decimal("85180"),
                    refunds=Decimal("2905"), product_cost=Decimal("25390"), ad_spend=Decimal("12300"),
                    fba_fee=Decimal("6814"), referral_fee=Decimal("8518"), contribution_profit=Decimal("17253")),
        ],
        ad_campaigns=[
            AdCampaignData(campaign_id="CAMP-001", campaign_name="自动广告-核心词",
                          spend=Decimal("87500"), sales=Decimal("312500"), impressions=125000, clicks=3200),
            AdCampaignData(campaign_id="CAMP-002", campaign_name="手动广告-长尾词",
                          spend=Decimal("62500"), sales=Decimal("268000"), impressions=85000, clicks=2100),
            AdCampaignData(campaign_id="CAMP-003", campaign_name="品牌广告-展示",
                          spend=Decimal("37500"), sales=Decimal("125000"), impressions=48000, clicks=980),
        ],
    )
    return compute_metrics(data)


def load_csv_data(csv_path: str) -> ProfitHealthData:
    """从 CSV 文件加载数据（简化版：只读汇总行）"""
    # TODO: 正式版需要完整实现 Settlement CSV 解析
    data = ProfitHealthData(period=os.path.basename(csv_path).replace(".csv", ""))

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row.get("metric", "")
            val = Decimal(row.get("value", "0"))
            if key == "total_sales":
                data.total_sales = val
            elif key == "refunds":
                data.refunds = val
            elif key == "product_cost":
                data.product_cost = val
            elif key == "ad_spend":
                data.ad_spend = val
            elif key == "referral_fee":
                data.referral_fee = val
            elif key == "fba_fee":
                data.fba_fee = val
            elif key == "net_profit":
                data.net_profit = val
    return compute_metrics(data)


def load_json_data(json_path: str) -> ProfitHealthData:
    """从 JSON 文件加载数据"""
    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    data = ProfitHealthData(
        period=raw.get("period", "未知期间"),
        total_sales=Decimal(str(raw.get("total_sales", 0))),
        refunds=Decimal(str(raw.get("refunds", 0))),
        product_cost=Decimal(str(raw.get("product_cost", 0))),
        ad_spend=Decimal(str(raw.get("ad_spend", 0))),
        referral_fee=Decimal(str(raw.get("referral_fee", 0))),
        fba_fee=Decimal(str(raw.get("fba_fee", 0))),
        fba_storage=Decimal(str(raw.get("fba_storage", 0))),
        net_sales=Decimal(str(raw.get("net_sales", 0))),
        net_profit=Decimal(str(raw.get("net_profit", 0))),
    )
    return compute_metrics(data)


# ═══════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="OP-006 Validation Build: Amazon 利润体检报告生成器")
    parser.add_argument("--sample", action="store_true", help="使用内置样例数据生成报告")
    parser.add_argument("--csv", type=str, help="输入 CSV 文件路径（key-value 格式）")
    parser.add_argument("--json", type=str, help="输入 JSON 文件路径")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="输出路径（默认：reports/profit-health-report-{date}.md）")
    parser.add_argument("--report-dir", type=str,
                        default=str(PROJECT_ROOT / "reports"),
                        help="报告输出目录（默认：./reports/）")
    args = parser.parse_args()

    # 1. 加载数据
    if args.sample:
        data = load_sample_data()
        print("📊 使用内置样例数据")
    elif args.csv:
        data = load_csv_data(args.csv)
        print(f"📊 从 CSV 加载数据：{args.csv}")
    elif args.json:
        data = load_json_data(args.json)
        print(f"📊 从 JSON 加载数据：{args.json}")
    else:
        print("⚠️  未指定数据源，使用内置样例数据\n")
        data = load_sample_data()

    # 2. 运行诊断
    print(f"🔍 运行经营诊断...")
    provider = MockDiagnosisProvider()
    target_data = {}
    if data.target_profit:
        target_data["net_profit"] = float(data.target_profit)
    if data.target_ad_rate:
        target_data["ad_spend_rate"] = float(data.target_ad_rate)
    if data.net_margin:
        target_data["net_profit_margin"] = 10.0  # 行业合理净利率基准
    target_data["return_rate"] = 3.0  # 行业基准

    diagnosis = provider.diagnose(
        {
            "net_profit": data.net_profit,
            "ad_spend_rate": data.ad_spend_rate,
            "net_profit_margin": data.net_margin,
            "return_rate": data.return_rate,
            "affected_skus": [s.sku for s in data.skus if s.contribution_profit < 0],
        },
        target_data,
    )
    print(f"   → 发现 {len(diagnosis.abnormal_items)} 项异常")

    # 3. 确定输出路径
    output_path = args.output
    if not output_path:
        date_str = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_dir = args.report_dir
        os.makedirs(report_dir, exist_ok=True)
        output_path = os.path.join(report_dir, f"profit-health-report-{date_str}.md")

    # 4. 生成报告
    print(f"📝 生成利润体检报告...")
    report = generate_report(data, diagnosis, output_path=output_path)
    print(f"✅ 报告生成完成")
    print(f"📄 {output_path}")
    print(f"📏 {len(report)} 字符, {report.count('##')} 个章节")

    # 5. 打印摘要
    print(f"\n{'='*50}")
    print(f"📊 经营摘要")
    print(f"{'='*50}")
    print(f"  总销售额：¥{float(data.total_sales):,.0f}")
    print(f"  净利润：  ¥{float(data.net_profit):,.0f}（{data.net_margin:.1f}%）")
    print(f"  广告占比：{data.ad_spend_rate:.1f}%")
    print(f"  退款率：  {data.return_rate:.1f}%")
    print(f"  TACOS：   {data.tacos:.1f}%")
    print(f"  异常项：  {len(diagnosis.abnormal_items)} 项")
    print(f"{'='*50}")
    print(f"\n💡 提示：报告内容可直接复制到飞书文档")


if __name__ == "__main__":
    main()
