# n8n 与 Coze 3.0 分析参考

> 来源：GPT 分析（2026-06），经 Hermes 整理归档
> 相关：AI Company OS Runtime Registry + Adapter Layer 设计

---

## 一、n8n

### 是什么

可视化自动化流程编排工具。开源自托管的 Zapier/Make。

### 核心能力

```
触发器 → 流程节点 → AI Agent → 工具调用 → 人工审批 → 外部系统集成
```

- 支持 Docker Compose 自部署（官方提供 self-hosted AI Starter Kit）
- AI Agent 节点可调用工具
- 敏感动作支持 human-in-the-loop 审批

### 适合场景

| 场景 | 说明 |
|:-----|:------|
| 定时数据抓取 | 每天早上抓 RSS / GitHub / Product Hunt / Reddit |
| Webhook 接收 | 表单提交 / 客户反馈自动入库 |
| 通知流转 | 飞书 / 邮件 / Slack 消息推送 |
| 轻量审批 | AI 判断后暂停，等人批准再执行 |
| 数据同步 | Google Sheet / 数据库 / CRM 之间搬运 |
| 内容运营 | 生成本周发布清单、提醒 Founder |

### 不适合

- 替代 OS 控制平面（不要用 n8n 调度 Codex/Claude 做代码开发）
- 核心代码变更
- 复杂业务逻辑编排

### AI Company OS 中的定位

```
AI Company OS = 公司控制平面（决策 / 治理 / 资产 / 审计）
n8n          = 自动化执行器 / Runtime 之一
```

关系：OS 是大脑，n8n 是自动化管道工。

### 接入时机

当前已登记为 `planned` runtime type，**暂不部署**。

出现以下情况时值得上 n8n：

- 每天抓取 10+ 信息源
- 每周生成固定报告
- 客户反馈需要自动分类和通知
- 飞书 / 表格 / 邮件之间反复搬运数据
- 内容发布日历需要自动提醒

### 借鉴的思想

即使不用 n8n，其工作流模板值得吸收：

```
Trigger    →  什么触发？
Input      →  输入是什么？
AI Step    →  AI 做什么判断？
Tool Step  →  调用什么工具？
Human Review → 哪里需要人审批？
Output     →  产出写到哪里？
Log        →  过程怎么记录？
```

这与 AI Company OS 的 Runtime Task Contract 高度一致。

---

## 二、Coze 3.0（扣子）

### 是什么

项目空间 + Agent 团队 + 本地/云端 Agent 接入平台。

早期是 Bot / Agent 开发平台，3.0 升级为：
- 多 Agent 项目空间
- 支持接入本地 Claude Code CLI / Codex CLI / OpenClaw
- 本地 Agent 可与云端 Agent 在同一个项目空间协作
- 资产可沉淀

### 与 AI Company OS 的相似点

| 维度 | Coze 3.0 | AI Company OS |
|:-----|:---------|:--------------|
| 多 Agent | ✅ Agent 团队 | ✅ CEO Agent + 子 Agent + Codex/Claude |
| 项目空间 | ✅ Project Space | ✅ product_line + project 视图 |
| 本地 Agent 接入 | ✅ Claude / Codex / OpenClaw | ✅ Runtime Registry 规划中 |
| 资产沉淀 | ✅ | ✅ Asset Registry 规划中 |

### 关键启发

市场方向被验证了——"Project Space + Agent Team + Local Runtime" 不是自嗨。

### 差异定位

```
Coze 3.0       = Agent 怎么一起工作（Agent 工作空间平台）
AI Company OS  = Founder 怎么用 AI Team 经营一家公司
                （机会 / 产品线 / 成本 / 审计 / 学习 / 增长）
```

### 接入策略

**❌ 不接入。** 原因：

1. 核心方法论和资产在 `private/` OS 里，不适合迁入外部平台
2. Coze 是外部平台，引入平台绑定风险
3. AI Company OS 需要的成本控制、审计、产品线组合、Founder Review 不是 Coze 的核心能力
4. 长期目标是自建 Operating System，不是把方法论塞进别人的平台

当前位置：`runtime-registry.yaml` 中登记为 `reference_only`。

---

## 三、定位对比

```
n8n            = 自动化流水线工人
Coze 3.0       = 另一个公司的工作空间（参考对象 / 竞品信号）
AI Company OS  = 你自己的公司总部 / 总控室
Hermes         = CEO 助理 + 调度官
Codex/Claude   = 程序员员工
OpenClaw       = 后台自动员工
```

---

## 四、当前处理策略

| 工具 | 处理 | 说明 |
|:-----|:-----|:------|
| **n8n** | `planned` 不部署 | runtime-registry 中已登记，等出现明确重复运营流程再上 |
| **Coze** | `reference_only` 不接入 | 研究其 Project Space + Local Agent Bridge 设计，但不把 OS 迁入 |
| **Codex** | ✅ active，半自动 | v0.45 已跑通 Task Card 派活，v0.45.2 做 Adapter 硬化 |
| **Claude** | ✅ active，manual | 先做 manual_adapter，不急着自动化 |

---

## 五、优先级建议

```
第一优先：v0.45.x — Runtime Runner + Codex Adapter 硬化（当前工作）
第二优先：n8n — 保持 planned，不部署
第三优先：Coze — 保持 reference_only，持续关注
```

---

*归档日期：2026-06-03*
*来源：Hermes + GPT 联合分析*
