# LLM-INTEGRATION-PLAN.md — AI经营系统真实 LLM 接入方案

> **范围：** 不涉及完整开发，只做方案设计
> **第一版只接：** abnormal_diagnosis Skill
> **其他 4 个 Skill：** 后置
> **前提：** 冷启动有付费信号后，按此方案实施

---

## 一、架构总览

```
┌─────────────────────────────────────────────────────┐
│                  LLM Gateway                         │
│                                                       │
│  ┌──────────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ ProviderConfig│  │ LLMClient│  │ SchemaValidator │  │
│  │ (可配置)      │  │          │  │ (输出校验)     │  │
│  └──────┬───────┘  └────┬─────┘  └───────┬────────┘  │
│         │               │               │            │
│  ┌──────┴───────┐  ┌────┴─────┐  ┌──────┴────────┐  │
│  │ PromptRunner │  │ CostLog  │  │ Fallback Mock  │  │
│  │ (Skill专用)  │  │ (记录)   │  │ (兜底)        │  │
│  └──────────────┘  └──────────┘  └───────────────┘  │
└─────────────────────┬───────────────────────────────┘
                      │
            ┌─────────▼─────────┐
            │  abnormal_diagnosis │
            │  Skill (真实LLM版)  │
            └───────────────────┘
```

---

## 二、组件设计

### 2.1 LLMClient

**现有基础：** `app/services/llm_client.py` 已有 3-tier provider chain + structured output parsing

**改动：**
- 从"API key 存在就尝试"改为"显式配置 default provider"（`LLM_PROVIDER=minimax`）
- 增加 `completion()` 方法（现有 `complete_structured()` 保留）
- 增加 `is_available()` 健康检查方法
- 失败时返回 `LLMResult(success=False, fallback_to_mock=True, ...)`

### 2.2 ProviderConfig

```python
class ProviderConfig:
    default_provider: str = "minimax"       # minimax / deepseek / openai / mock
    minimax_api_key: str = ""
    minimax_model: str = "abab-7"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    fallback_order: list = ["minimax", "deepseek", "openai", "mock"]
    max_retries: int = 3
    retry_delay: int = 2  # seconds
    timeout: int = 30      # seconds
    max_tokens: int = 4096
```

**环境变量加载：** 从 `.env` 或 os.environ 加载，支持运行中切换

### 2.3 PromptRunner

**职责：** 为 abnormal_diagnosis 构建 LLM 提示词

```python
class PromptRunner:
    def build_abnormal_diagnosis_prompt(self, data_context: dict) -> str:
        """组装异常诊断提示词"""
        prompt = f"""
你是一个 Amazon 卖家利润分析专家。

## 当前经营数据
- 期间：{data_context['period']}
- 总销售额：¥{data_context['total_sales']}
- 净利润：¥{data_context['net_profit']}
- 广告费：¥{data_context['ad_spend']}
...

## 你的任务
分析上述经营数据，找出异常指标并给出 root cause。

请按以下 schema 输出：
...
"""
        return prompt
```

**设计原则：**
- 提示词与代码分离（未来可放入 prompts/ 目录）
- 提示词版本管理（prompt_version 字段）
- 支持批量/表格数据注入

### 2.4 SchemaValidator

**现有基础：** `packages/skills/abnormal_diagnosis/output_schema.json` 已有

**改动：**
- 增加 LLM 输出的后处理：去除 think 标签、JSON fence 解析（已有）
- 增加 Schema 强制修复：如果 LLM 输出缺少必填字段，用默认值补充
- 增加字段级别的置信度评分

### 2.5 CostLogger

```python
class CostLogger:
    def log_call(self, provider, model, prompt_tokens, completion_tokens,
                  duration_ms, success, error_msg=None):
        """记录每次 LLM 调用的成本和状态"""
        # 保存到 ai_analysis_runs 表（已有）
        # 计算成本：provider 单价 × token 数
```

**现有基础：** `app/services/llm_client.py` 已有 token/cost stats logging

**新增：**
- provider 级单价映射表
- 月度成本聚合
- LLM 调用成功率报表

### 2.6 FallbackMock

```python
class FallbackMock:
    def execute(self, skill_name, data_context):
        """当 LLM 全部不可用时，返回当前 mock 规则的结果"""
        # 调用现有的 _mock_rules_abnormal() 函数
        # 在结果中标记 "llm_unavailable"，不阻止报告生成
```

**设计原则：** 永不阻塞。LLM 失败 → 降级到规则版 → 报告仍可生成（标注"AI 分析不可用"）

---

## 三、Provider 可达性测试结果

| Provider | 端点 | 状态 | 延迟 | 备注 |
|:---------|:-----|:-----|:-----|:------|
| MiniMax M2.5 | `api.minimax.chat/v1/text/chatcompletion_v2` | ✅ 可达 | 待测 | 需有效 API Key |
| DeepSeek | `api.deepseek.com/chat/completions` | ✅ 可达 | 待测 | 需有效 API Key |
| OpenAI | `api.openai.com` | ❓ 未测 | — | 中国大陆可能不通 |
| Ollama（本地） | `localhost:11434` | ❓ 未测 | — | 需检查是否已安装 |

> ⚠️ **注意：** 可达性测试已确认 MiniMax 和 DeepSeek 从当前网络环境可以访问。
> 但功能测试（结构化输出、延迟、成本）需要有效 API Key 才能进行。

---

## 四、abnormal_diagnosis 真实 LLM 接入范围

### 输入的 Skill 数据

现有的 `_mock_rules_abnormal()` 已经可以计算：
- 实际 vs 目标的偏差（金额 + 百分比）
- 风险评级（low/medium/high/critical）
- 异常类型判定

**真实 LLM 接入后，LLM 负责的部分：**
1. ✅ 用自然语言解释异常原因（"为什么广告费突然涨了 40%"）
2. ✅ 推荐下一步行动（"建议暂停 CAMP-001，重新优化关键词"）
3. ✅ 识别规则无法发现的模式（"上个月销量下降是因为竞品在 Prime Day 期间大幅降价"）

**规则逻辑保留：** 偏差计算、风险评级仍然由 Python 规则完成（更准确、更可靠）

### 输出的 Skill 结构

```json
{
  "summary": "本月存在 3 项异常，总影响金额 ¥XX,XXX",
  "key_findings": [
    "广告费较目标超支 40%，主要来自 CAMP-001",
    "SKU-B 净利润率从 12% 降至 5%，已接近亏损线",
    "退款率从 3% 升至 7%，建议检查产品质量"
  ],
  "abnormal_items": [
    {
      "metric": "ad_spend",
      "actual": 125000,
      "target": 89000,
      "variance": 36000,
      "variance_pct": 40.4,
      "severity": "high",
      "root_cause": "CAMP-001 在 5 月 15 日突然提高竞价，ACOS 从 12% 升至 28%",
      "recommendation": "建议暂停 CAMP-001，重新优化关键词匹配方式"
    }
  ],
  "recommendations": [
    "暂停 CAMP-001 广告活动",
    "SKU-B 价格调整至盈亏平衡线以上",
    "检查近期差评和产品质量反馈"
  ]
}
```

**注意：** 这种结构是 **LLM 填充 root_cause 和 recommendation**，异常检测的逻辑（偏差计算、风险评级）仍由规则完成。

---

## 五、不进入首版 LLM 接入的能力

| 能力 | 原因 | 何时接入 |
|:-----|:------|:---------|
| 其他 4 个 Skill（budget/forecast/meeting/sku） | abnormal_diagnosis 对利润报告最核心 | 利润报告稳定后 |
| Image/PDF 分析 | 首版只处理 CSV | 用户需求明确后 |
| Streaming 输出 | 首版生成完整报告 | 需要实时分析时 |
| 多轮对话 | 首版是一次性报告 | 报告+咨询模式后 |
| Function Calling / Tool Use | 首版不需要 | 需要操作数据时 |

---

## 六、方案总结

| 维度 | 结论 |
|:-----|:------|
| 架构改动范围 | ✅ 小 — 增强现有 LLMClient，不改基础设施 |
| Provider 依赖 | ✅ Provider-agnostic — ProviderConfig 可无缝切换 |
| 降级能力 | ✅ 永不阻塞 — LLM 失败 → 规则版 |
| 成本控制 | ✅ CostLogger + 显式定价配置 |
| Schema 兼容 | ✅ 输出完全兼容现有 output_schema.json |
| 冷启动阻塞 | ❌ 不阻塞 — 冷启动期间手动生成报告，不需要 LLM |
| 下一步动作 | 冷启动有付费信号后实施（约 4-6h 工时） |
