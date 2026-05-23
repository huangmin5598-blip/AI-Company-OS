# AI Company Control Center v0.4 — Company Memory MVP PRD

> **状态**: 📋 PRD · 待执行
> **预估工时**: 10-14h（约 1.5-2 天冲刺）
> **定位**: v0.4 将已批准的 Learning Candidate 转化为可搜索、可引用、可被 CEO Agent 召回的组织记忆，让过去的失败、经验和判断开始影响未来的目标拆解与任务生成。
>
> **一句话**: v0.4 = Company Memory MVP — 让系统开始记住自己做了什么、做对了什么、做错了什么。
>
> **核心子系统**: Knowledge Pipeline

---

## 一、产品定位

### 从"产生经验"到"使用经验"

| 版本 | 核心能力 | 记忆状态 |
|:-----|:---------|:---------|
| v0.2 | Learning Candidate 生成 | 产生经验，但无后续 |
| v0.3 | CEO Agent 目标拆解 + 审批 | 使用经验，但无记忆支撑 |
| **v0.4** | **Learning Candidate → Org Memory → CEO Recall** | **经验可沉淀、可召回、可复用** |

### 主链路

```
Learning Candidate (approved)
  ↓ 自动生成
Knowledge Proposal (draft)
  ↓ Founder 确认格式 + 内容
Org Memory (FTS5)
  ↓ CEO Agent Goal Intake 前召回
Context Pack (referenced_memory_ids)
  ↓
更好的任务拆解 + 更准的 Context
```

### 回答的问题

> **我的系统能记住过去吗？**

v0.2 产生了经验（Learning Candidate）。
v0.3 让 Founder 的意图进入系统。
v0.4 回答：**"系统能记住过去的失败、决策和模式，并在下次遇到相似问题时自动想起吗？"**

---

## 二、范围

### 必做

| 模块 | 说明 | 优先级 |
|:-----|:------|:------:|
| **org_memory 表 (FTS5)** | 组织记忆表，支持全文搜索、状态管理、版本与替代 | P0 |
| **knowledge_proposals 表** | Knowledge Proposal 中间表，Learning Candidate → Org Memory 的审批桥接 | P0 |
| **POST .../from-learning-candidate/{id}** | 半自动生成 Knowledge Proposal，幂等 | P0 |
| **GET /api/v1/memory/search** | FTS5 搜索 org_memory，支持 business_line / memory_type 过滤 | P0 |
| **POST /api/v1/memory/recall** | CEO Agent 专用召回端点：输入目标摘要 → 返回 top 3 相关记忆 | P0 |
| **context_packs 加 referenced_memory_ids** | 独立字段，不复用 referenced_knowledge | P0 |
| **CEO Skill 增强** | Goal Intake 前调用 /recall，拆解结果引用 org_memory | P0 |
| **/memory 页面** | 搜索、过滤、查看来源链（Learning Candidate / Review / Task / Goal Session） | P0 |
| **Knowledge Proposal 确认流程** | 前端 /memory 页支持 approve / revise / reject proposal | P1 |

### 不做

| 不做 | 原因 |
|:-----|:------|
| ❌ Monitor Agent | → v0.5 |
| ❌ 自动修复 | → v0.6 |
| ❌ 自动写 AI-Knowledge-OS | → v0.4.1 |
| ❌ 向量数据库 / 复杂 RAG | FTS5 够用 |
| ❌ 完整 L1/L2/L3/L4 记忆架构 | 渐进实现 |
| ❌ Agent Meeting | → v0.8 |
| ❌ 多 Runtime | → v0.7 |

---

## 三、架构

```
v0.2 Review Gate 产出
  ↓
Learning Candidate (approval_status=approved)
  ↓  [半自动] POST /api/v1/memory/from-learning-candidate/{id}
Knowledge Proposal (status=draft)
  ↓  [Founder 确认]
Org Memory (status=active, FTS5 indexed)
  │
  ├── CEO Agent Goal Intake 前
  │     ↓  POST /api/v1/memory/recall
  │     Top 3 相关记忆
  │     ↓  拆解结果 + memory_references
  │
  └── Context Pack 引用
        referenced_memory_ids = [id1, id2, id3]
```

### 数据流

```
Approved Learning Candidate
  → 校验是否已生成 proposal (幂等)
  → 自动生成 Knowledge Proposal (draft)
  → Founder 在 /memory 页面确认
  → 写入 org_memory (status=active, version=1)
  → FTS5 索引建立
  → CEO Agent 下次拆解相似目标时召回
```

---

## 四、数据模型

### 4.1 knowledge_proposals

```sql
字段名                    类型          说明
────────────────────────────────────────────────────────────
id                        Integer PK
source_candidate_id       Integer       FK → learning_candidates.id
proposal_type             String        failure_pattern / decision_pattern / tool_gap / context_update / sop_hint
title                     String
summary                   Text
structured_content        Text          JSON: 建议的结构化内容
target_memory_type        String        mapped from proposal_type
business_line             String
status                    String        draft / approved / revised / rejected / expired
founder_notes             Text          Founder 确认时的备注
created_at                DateTime
approved_at               DateTime
```

### 4.2 org_memory

```sql
字段名                    类型          说明
────────────────────────────────────────────────────────────
id                        Integer PK
memory_type               String        failure_pattern / decision_pattern / tool_gap / context_update / sop_hint
title                     String
summary                   Text
content                   Text          结构化知识内容
business_line             String
tags                      Text          JSON: 标签数组
source_type               String        learning_candidate / review / task / manual
source_id                 String        来源 ID
source_candidate_id       Integer       FK → learning_candidates.id (nullable)
source_task_id            Integer       FK → task_pool.id (nullable)
source_review_id          Integer       FK → reviews.id (nullable)
source_goal_session_id    Integer       FK → goal_sessions.id (nullable)
confidence                Float         0.0-1.0
status                    String        active / superseded / expired / archived
version                   Integer       默认 1
supersedes_memory_id      Integer       被替代的记忆 ID (nullable)
export_status             String        not_exported / exported / pending / failed
knowledge_os_path         String        对应 AI-Knowledge-OS 的文件路径 (nullable)
knowledge_os_slug         String        对应 AI-Knowledge-OS 的 page slug (nullable)
created_at                DateTime
updated_at                DateTime
```

**FTS5 虚拟表：**

```sql
CREATE VIRTUAL TABLE org_memory_fts USING fts5(
  title, summary, content, tags,
  content='org_memory',
  content_rowid='id'
);
```

### 4.3 context_packs 字段追加

在已有 `context_packs` 表新增：

```sql
referenced_memory_ids     Text          JSON: [memory.id, ...] (独立字段，不复用 referenced_knowledge)
```

---

## 五、API 端点

### 新增端点

| 端点 | 方法 | 功能 |
|:-----|:----:|:-----|
| `/api/v1/memory/knowledge-proposals` | GET | 列表（按 status / type / business_line 筛选） |
| `/api/v1/memory/knowledge-proposals` | POST | 手动创建 proposal |
| `/api/v1/memory/knowledge-proposals/{id}/decide` | PATCH | Founder 确认 / 修改 / 拒绝 |
| `/api/v1/memory/from-learning-candidate/{id}` | POST | **幂等**：从已批准的 Learning Candidate 自动生成 proposal |
| `/api/v1/memory/entries` | GET | 列表（支持 business_line / memory_type / status 筛选） |
| `/api/v1/memory/entries/{id}` | GET | 详情（含来源链） |
| `/api/v1/memory/search` | GET | FTS5 全文搜索（q / business_line / memory_type 参数） |
| `/api/v1/memory/recall` | POST | CEO Agent 召回：输入目标摘要 → top 3 相关记忆 |

### 复用端点（已有，需确认可调）

| 端点 | 用途 |
|:-----|:------|
| `GET /api/v1/learning-candidates` | 查询已批准的 candidate |
| `PATCH /api/v1/learning-candidates/{id}/decide` | 审批 candidate |
| `GET /api/v1/reviews/{id}` | 查询 review 来源 |
| `GET /api/v1/task-pool/{id}` | 查询 task 来源 |
| `GET /api/v1/ceo/goal-sessions/{id}` | 查询 goal session 来源 |

---

## 六、前端页面

### 6.1 Memory 页面（新增 `/memory`）

功能：
- FTS5 全文搜索框
- 按 business_line 过滤
- 按 memory_type 过滤（failure_pattern / decision_pattern / tool_gap / context_update / sop_hint）
- 结果展示：
  - 标题、摘要、记忆类型标签、business_line
  - 状态（active / superseded / expired）
  - **来源链**：显示完整的来源追溯
  ```
  org_memory #12 ← learning_candidate #3 ← review #2 ← task #1 ← goal_session #1
  ```
- 点击展开详情：完整 content、tags、confidence、版本历史
- Knowledge Proposal 待审批条数 badge

### 6.2 Knowledge Proposals 面板（嵌入 /memory 页面或独立 tab）

- 待处理的 proposals 列表（status=draft）
- 每条显示：标题、类型、来源 candidate ID、摘要
- 操作按钮：Approve / Revise / Reject
- 已处理的 proposals 可查看历史

---

## 七、CEO Skill 增强

### Goal Intake 新增步骤

在拆解目标前，CEO Agent 执行：

```
1. 调用 POST /api/v1/memory/recall
   输入: { "goal_summary": "当前目标摘要", "business_line": "inferred" }
   返回: top 3 相关 org_memory

2. 拆解结果加入 memory_references:
    {
      "memory_references": [
        { "memory_id": 12, "title": "Amazon seller API 400", "reason": "当前目标与此历史失败模式相似" }
      ]
    }

3. 创建的 Context Pack 写入 referenced_memory_ids
```

### 安全规则

- 召回是辅助参考，不是约束。CEO Agent 仍可独立判断
- 召回结果仅供拆解参考，不强制影响拆解逻辑
- 若召回为空，不影响拆解正常进行

---

## 八、安全边界

| 边界 | 实现 |
|:-----|:------|
| 不自动写入 org_memory | Knowledge Proposal 需要 Founder 确认 |
| 不自动写 AI-Knowledge-OS | 预留 export 字段，不自动同步 |
| 幂等保障 | from-learning-candidate 幂等，不重复生成 |
| 记忆版本控制 | version + supersedes_memory_id 支持替代 |
| 记忆过期 | status=expired 支持废弃 |
| 召回不影响安全门 | 召回仅供参考，不绕过 Command Center / Approval |

---

## 九、验收标准

### 验收 1：Learning Candidate → Org Memory

**输入：** 一个已批准的 Learning Candidate（learning_candidates.approval_status=approved）

**系统结果：**
1. ✅ `POST /api/v1/memory/from-learning-candidate/{id}` 返回 200
2. ✅ `knowledge_proposals` 新增 1 条（status=draft）
3. ✅ 重复调用幂等（不创建重复 proposal）
4. ✅ Founder 确认后 → `org_memory` 新增 1 条（status=active, version=1）
5. ✅ FTS5 索引已建立，可通过 `/api/v1/memory/search` 搜索到

### 验收 2：CEO Agent 召回

**输入：**
> 亚马逊选品又失败了，帮我排查。

**系统结果：**
1. ✅ 调用 `POST /api/v1/memory/recall` 返回 top 3 相关记忆
2. ✅ 拆解结果包含 `memory_references`
3. ✅ Context Pack 包含 `referenced_memory_ids`

### 验收 3：Memory 页面

**系统结果：**
1. ✅ `/memory` 页面可搜索关键词
2. ✅ 可按 business_line / memory_type 过滤
3. ✅ 显示完整来源链（candidate → review → task → goal_session）

---

## 十、不做清单（速查）

```text
❌ Monitor Agent
❌ 自动修复
❌ 自动写 AI-Knowledge-OS
❌ 向量数据库 / 复杂 RAG
❌ 完整 L1/L2/L3/L4 记忆架构
❌ Agent Meeting
❌ 多 Runtime
❌ 自动扫描全系统
❌ 自动改代码
❌ 自动改 OpenClaw
```

---

> **v0.4 Company Memory MVP**
>
> 让系统开始记住自己做了什么、做对了什么、做错了什么。
>
> Learning Candidate → Knowledge Proposal → Org Memory → CEO Agent Recall
>
> 等系统能记住，v0.5 再让它开始主动观察。
