# CAPABILITY-MAPPING.md — AI经营系统 v0.1 → 利润体检报告首版能力对照

> **对照范围：** AI经营系统 v0.1（已有能力）vs Amazon 利润体检报告首版（需要的能力）
> **时间：** 2026-05-29
> **结论：** 🟢 覆盖约 70%，核心缺口是 LLM 接入 + Settlement 导入

---

## 一、矩阵总览

| 维度 | 已有 | 可复用模块 | 缺口 | 可后置 | 不进入首版 |
|:-----|:----|:----------|:-----|:------|:----------|
| 数据模型 | 5 个事实表（sales/profit/ads/inventory/sku_costs） | ✅ 直接匹配 | Settlement Report 特有字段 | Session 管理 | — |
| 数据导入 | CSV 导入管线（preview → upload → confirm） | ✅ 可复用 | Settlement CSV 解析器 | 多渠道数据 | SP-API 自动同步 |
| LLM | 3-tire provider chain + Mock fallback | ✅ 架构可复用 | 真实 LLM 接入（只接 abnormal_diagnosis） | 其他 4 个 Skill | — |
| Skill 引擎 | 5 个 Skill + registry + runner | ✅ 2 个直接匹配 | — | 其他 3 个 Skill | 完整 AI Seller Finance |
| 报告生成 | 13 章节 DOCX 报告 | ✅ 框架可复用 | 利润报告模板 | 多格式导出 | — |
| 异常诊断 | abnormal_diagnosis_skill（规则版） | ✅ 输出结构可用 | LLM 驱动的异常解释 | 更深层原因分析 | — |
| 广告分析 | ads_facts + ACOS/ROAS 计算 | ✅ 直接匹配 | 广告效率标签（偏高/合理） | 自动优化建议 | 完整广告分析 |
| 前端 | 15 个 Next.js 页面 | 🔶 可复用 AI 对话面板 | 上传版报告页面 | 报告历史列表 | 完整 Dashboard |
| 用户系统 | auth + roles（owner/finance/admin/operations） | 🔶 可复用 | 卖家侧的简化用户模型 | 多店铺管理 | — |
| Amazon API | 无 | — | Settlement Report 解析引擎 | 广告报告解析 | SP-API 全套 |

---

## 二、已有能力（🟢 14 项）

### P0 — 直接用于利润体检报告

| 能力 | 来源 | 说明 |
|:-----|:-----|:------|
| `profit_facts` 数据模型 | DB schema | 含 sales_amount, product_cost, platform_fee, fba_fee, shipping_cost, ad_spend, contribution_profit |
| `sales_facts` 数据模型 | DB schema | 含 units_sold, gross_sales, net_sales, refunds |
| `ads_facts` 数据模型 | DB schema | 含 spend, sales, impressions, clicks, ACOS, ROAS |
| `sku_costs` 数据模型 | DB schema | 含 product_cost, shipping, platform_fee, fba_fee |
| `overview.py` 聚合函数 | backend service | 已实现 Net Sales、Contribution Profit、Ad Spend、TACOS 计算 |
| CSV 导入管线（sales/profit/ads） | imports.py | preview → upload → confirm 全流程跑通 |
| abnormal_diagnosis_skill | skill_runner.py | 异常检测的 output_schema（summary, key_findings, abnormal_items, root_causes）可直接复用 |
| sku_lifecycle_diagnosis_skill | skill_runner.py | SKU 分类逻辑（Launch/Growth/Mature/Decline） |
| Skill Runner 框架 | skill_runner.py | 输入验证 → 上下文组装 → 执行 → 持久化 全链路 |
| DOCX 报告 Builder | docx_report_builder.py | 13 章节框架，可复用封面、表格、免责声明模板 |
| 决策/行动项系统 | decisions service | 完整的提议 → 记录 → 追踪生命周期 |
| AI 对话面板 + Guardrails | page_chat_service.py | 可嵌入报告页面的 AI 问答 |
| LLM Client 架构 | llm_client.py | Provider chain（MiniMax → DeepSeek → Ollama → Mock）+ structured output parsing |
| 知识库系统 | knowledge service | 文档存储 + chunking |

### P1 — 需调整但不阻塞首版

| 能力 | 来源 | 调整需求 |
|:-----|:-----|:---------|
| business_review_meeting_skill | skill_runner.py | 会议结构可包装利润报告，但需要新的上下文构建器 |
| cost allocation engine | allocation_engine.py | 分摊逻辑可复用，但需要 Amazon 特有费用分摊方法 |
| financial check service | financial_check_service.py | 检查框架可复用，检查项需替换为 Amazon 特有维度 |
| 用户登录/auth | auth service | 首版可以简化，直接接受文件不上传用户系统 |

---

## 三、缺口能力（🔴 4 项）

### 必须补的（阻塞首版交付）

| 缺口 | 严重性 | 为什么需要 | 最小方案 |
|:-----|:-------|:----------|:---------|
| LLM 真实接入（abnormal_diagnosis 接入） | 🔴 | 现在 Skill 跑的是 Python 规则，不是 LLM。利润报告需要 LLM 解释"为什么利润变了" | 只接 abnormal_diagnosis，其他 4 个后置 |
| Settlement Report 解析引擎 | 🔴 | 卖家给的是 Amazon Settlement Report CSV，不是现有 import 系统支持的格式 | 专门解析 Settlement 的 CSV 解析器，首版接受单店铺单月 |
| 利润报告输出模板 | 🟡 | 现有 DOCX 报告是经营分析会风格，不是卖家利润报告风格 | 新建利润报告模板（见 SAMPLE-REPORT-TEMPLATE.md） |
| 文件上传（Settlement Report） | 🟡 | 现有上传系统只支持固定 Schema 的 CSV，不支持 Settlement 原始格式 | 在现有 imports 管线增加 settlement 类型 |

### 可后置的（第三版再说）

| 缺口 | 说明 |
|:-----|:------|
| SP-API 自动同步 | 首版手动上传，自动同步后期再说 |
| 多店铺支持 | 首版单店铺 |
| 广告 Report 自动解析 | 首版用 ads_facts 已有数据即可 |
| 库存成本自动计算 | 首版用 sku_costs 已有数据 |
| 汇率自动换算 | 跨境卖家的刚需，但首版先支持单一币种 |

### 不进入首版的

| 能力 | 原因 |
|:-----|:------|
| 完整 SaaS（多页面/多用户/订阅管理） | 先验证付费意愿 |
| 金蝶/用友对接 | 后期再说 |
| ERP 对接 | 后期再说 |
| 多平台（Shopify/TikTok/Shopee） | 先只做 Amazon |
| 复杂 Dashboard | 首版只要报告 PDF/H5 |

---

## 四、技术栈对照

| 层 | AI经营系统 v0.1 | 利润体检报告首版 | 变化 |
|:---|:---------------|:----------------|:-----|
| 后端 | FastAPI + SQLite | FastAPI + SQLite（复用） | 不变 |
| 前端 | Next.js 14 | 首版不需要前端，直接发报告 | 简化 |
| 数据库 | SQLite 37 表 | 复用 profit/sales/ads_facts + 新增 settlement_imports 表 | +1 表 |
| LLM | Mock → 3-tier provider chain | 真实 LLM（只接 abnormal_diagnosis） | 改 1 个 Skill |
| 导入 | CSV imports | + Settlement CSV 解析 | 改 imports |
| 报告 | DOCX 13 章节 | 新建利润报告模板 | 新建 |

---

## 五、结论：开发工时预估

| 模块 | 工时 | 依赖 |
|:-----|:-----|:------|
| LLM 集成（abnormal_diagnosis） | 4-6h | ❌ 阻塞 — 冷启动有付费信号才启动 |
| Settlement CSV 解析器 | 6-8h | ❌ 阻塞 |
| 利润报告模板 | 2h | ✅ 可以先做（本文件本身就是模板） |
| 文件上传 Settlement 类型 | 2h | ❌ 阻塞 |
| 端到端测试 | 2h | — |
| **总计** | **~16-18h** | **当前不做** |
