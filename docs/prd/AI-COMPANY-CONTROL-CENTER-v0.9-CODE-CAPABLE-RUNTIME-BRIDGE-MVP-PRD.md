# AI Company Control Center v0.9 — Code-Capable Runtime Bridge MVP PRD

> **状态**: 📋 PRD · 待执行
> **预估工时**: 11-13h（分 Sprint A0 + Sprint A + Sprint B + Sprint C）
> **定位**: v0.9 将 Codex / Claude Code 等 Code-Capable Runtime 接入 AI Company OS 的受控执行桥，让系统可以在 Founder 看得懂、可确认、可回滚的安全流程下完成低风险代码修改。
>
> **一句话**: v0.9 = Code-Capable Runtime Bridge — 让非技术 Founder 可以安全地指挥 Coding Agent 改代码，不审 diff，只看摘要。
>
> **核心子系统**: Execution Request → Code Change Request → Coding Agent Plan → Staging + Isolated Check Workspace → Automated Checks → Founder Review → Apply/Rollback

---

## 一、产品定位

### 从"安全执行低风险动作"到"安全执行代码修改"

| 版本 | 核心能力 | 创始人角色 |
|:-----|:---------|:-----------|
| v0.7 | Improvement Proposal | 读提案、批准/驳回 |
| v0.8 | Controlled Execution Bridge 5 Safe Actions | 确认执行、验证结果（不涉及代码） |
| **v0.9** | **Code-Capable Runtime Bridge** | **读自然语言方案 → 确认 → 看结果 → 关闭** |
| v1.0 | Agent Meeting Session | 主持会议、做决策 |

### 为什么要现在做

v0.8 的执行桥已经能安全执行诊断/检查/草稿类动作，但 **modify_code 仍然是 blocked action**（白名单里写了 "延迟到 v0.9"）。

对于 AI Company OS 来说，最有价值的改进往往是代码修改：
- 修复 UI bug（按钮状态不对、列表渲染异常）
- 添加小功能（新的看板卡片、过滤条件）
- 优化提示文案和交互

v0.9 的目标不是"让 AI 自动写代码"，而是让非技术创始人 **安全地指挥 AI 写代码** —— 流程保护、摘要决策、一键回退。

### 四条安全原则

1. **不直接改 main** — 所有修改先写入 staging 区，apply 只到本地工作区
2. **不自动 deploy** — 应用只到本地工作区，commit/push/deploy 后置
3. **Protected files 硬拦截** — .env/.db/secrets/credentials/deploy config/数据库迁移等碰到就拒绝
4. **一步一确认** — Plan 阶段确认、Checks 后确认、Apply/Keep/Rollback

---

## 二、范围

### 必做

| 模块 | 说明 | 工时 |
|:-----|:------|:----:|
| **A0: Code Runtime Capability Spike** | 确认 Codex/Claude Code CLI 可用性、非交互能力、workspace 限制 | 1h |
| Code-Capable Runtime 抽象接口 | runtime_type=codex / claude_code 能力发现 + plan/patch/check | 1.5h |
| Codex Adapter | 真实集成 Codex CLI（generate_plan / generate_patch / run_checks） | 2h |
| Claude Code Adapter Shape | adapter 结构 + capability discovery，不要求完整流程 | 0.5h |
| `code_change_requests` 表 | 独立表，关联 execution_request_id | 1h |
| Plan → Patch → Checks 后端链路 | 状态机 + 路由 | 2h |
| Staging + Isolated Check Workspace | `.ai-company-os/staging/{request_id}/` + `check_workspace/` 隔离检查 | 1.5h |
| Protected Files 策略（双层检查） | Pre-check files_expected + Post-check patch.diff/files_changed | 0.5h |
| Rollback 机制 + 路径安全校验 | rollback_manifest.json + safe_path_join | 0.5h |
| Founder 前端界面 | 摘要展示、确认、回退按钮 | 1.5h |

### Action Type 白名单（v0.9 新增）

v0.8 的 5 种 safe action **全部保留不变**。新增 code 类 action：

| Action Type | 说明 | 关联 | 是否需要 Code-Capable Runtime |
|:------------|:-----|:-----|:------------------------------|
| `generate_code_plan` | Coding Agent 分析代码 → 生成自然语言方案 | code_change_request | ✅ |
| `generate_patch` | Coding Agent 执行方案 → 生成 patch 到 staging | code_change_request | ✅ |
| `run_code_checks` | 在 isolated check_workspace 中运行 build/lint/typecheck | code_change_request | ✅ |
| `apply_patch_to_workspace` | 将 staging patch 应用到实际工作目录 | code_change_request | ❌（Hermes 执行） |
| `rollback_patch` | 按 manifest 回退已应用的文件 | code_change_request | ❌（Hermes 执行） |

### 仍然不允许（策略拦截 — 即使 Founder 确认也不执行）

| Action | 原因 | 替代 |
|:-------|:-----|:-----|
| `apply_patch_to_main` | 不直接改主分支 | 通过 staging apply |
| `deploy` | 生产风险 | 不进受控执行桥 |
| `create_github_pr` | 后置到 v0.9.1 / v1.1 | 手动操作 |
| `auto_merge` | 不安全 | 不进受控执行桥 |
| `modify_protected_files` | .env/.db/secrets/credentials/迁移文件 | 硬拦截 |
| `modify_database_schema` | **v0.9 直接 blocked**。无迁移回滚系统 | 后置到独立版本 |
| `execute_high_risk_shell` | 安全风险 | 不进受控执行桥 |
| `auto_retry_on_failure` | 禁止无限循环 | v0.8 原则延续 |

### 状态机

**code_change_requests 独立状态机**：

```
draft
  → plan_generated         (Coding Agent 完成分析，生成自然语言方案)
  → plan_approved          (Founder 确认方案)
  → patch_generated        (Coding Agent 生成 patch 到 staging)
  → checks_running         (在 isolated check_workspace 中运行自动检查)
  → checks_passed          (所有检查通过)
  → checks_warning         (有非阻断性警告 — 需要 Founder 二次确认风险)
  → checks_failed          (有阻断性失败 — 只能 revise/retry/reject)
  → founder_review         (Founder 看到摘要 + 结果)
  → applied                (patch 应用到本地工作区)
  → rolled_back            (按 manifest 回退)
  → rejected               (Founder 拒绝整个请求)
```

**阻断规则**：
- `checks_failed` → 不能 apply。只能：`revise`（回退到 plan_approved 重跑）、`reject`（关闭）
- `checks_warning` → 可以 apply，但必须显式二次确认 + 记录 `applied_with_warning=true`
- `checks_passed` → 正常进入 founder_review

### 不做

- ❌ 完整 GitHub PR workflow（v0.9.1 / v1.1）
- ❌ 自动 merge
- ❌ 自动 deploy
- ❌ 自动 commit + push
- ❌ 数据库迁移执行
- ❌ 安全漏洞自动修复
- ❌ 跨 Runtime 自动选择 coding agent
- ❌ Agent Meeting Session（v1.0）
- ❌ 自动无限修复循环
- ❌ 自动写 Org Memory（延续 v0.8 原则）
- ❌ 多租户、权限系统、模板市场

---

## 三、系统设计

### 3.1 主线链路

```
Improvement Proposal approved (v0.7) 或其他来源 (Goal/Manual)
  ↓
Execution Request Created (action_type=code_change_request)
  ↓
Code Change Request Created (关联 execution_request_id)
  ↓
Stage 1: Generate Plan
  → 调 Codex / Claude Code 分析代码
  → 输出自然语言方案 (plan_summary + impact_scope)
  → 状态: plan_generated
  ↓
Founder 审阅方案
  → 看自然语言摘要、影响范围、风险评级
  → Approve / Revise / Reject
  ↓ (Approved)
Stage 2: Generate Patch + Prepare Workspaces
  → 复制 original_files/ 到 staging/original_files/
  → 调 Codex / Claude Code 生成 patch.diff
  → 将 patch 应用至 check_workspace/
  → 从 check_workspace/ 提取 modified_files/
  → 写入 .ai-company-os/staging/{request_id}/
  → 状态: patch_generated
  ↓
Stage 3: Automated Checks (in isolated check_workspace)
  → npm run build / python import check / lint
  → 写入 check_result.json + protected_file_check.json
  → 状态: checks_passed / checks_warning / checks_failed
  ↓
Stage 4: Founder Review
  → 看到自然语言摘要 + 影响范围 + 检查结果 + 手动验证步骤
  → Founder 打开页面/系统看效果
  → Apply / Rollback / Reject
  ↓ (Applied)
Execution Request verification_pending
  → Founder 手动验证功能
  → 确认成功后 closed_success
```

### 3.2 code_change_requests 表

```sql
CREATE TABLE code_change_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,
    -- improvement_proposal / goal / manual
    source_id TEXT,
    execution_request_id INTEGER NOT NULL,
    -- 关联 execution_requests (受控执行总入口)
    runtime_id TEXT,
    -- codex / claude_code
    title TEXT NOT NULL,
    -- 用户可理解的标题
    problem_summary TEXT,
    -- 要解决的问题（自然语言）
    plan_summary TEXT,
    -- Coding Agent 生成的自然语言方案
    impact_scope_json TEXT,
    -- JSON: 影响范围描述 { files, components, services }
    risk_level TEXT NOT NULL DEFAULT 'medium',
    -- low / medium / high
    files_expected_json TEXT,
    -- JSON: 预计修改的文件列表 (用于 pre-check)
    files_changed_json TEXT,
    -- JSON: 实际修改的文件列表 (用于 post-check)
    patch_path TEXT,
    -- 相对路径: .ai-company-os/staging/{id}/patch.diff
    diff_summary TEXT,
    -- 自然语言 diff 摘要（行数、文件数、改动类型）
    check_result_json TEXT,
    -- JSON: { build: { passed, output }, lint: { passed, warnings }, ... }
    protected_file_check_json TEXT,
    -- JSON: { pre_check: {...}, post_check: {...} }
    applied_with_warning INTEGER DEFAULT 0,
    -- checks_warning 时 apply 的记录标志
    status TEXT NOT NULL DEFAULT 'draft',
    -- 见独立状态机
    plan_approved_by TEXT,
    plan_approved_at TEXT,
    applied_by TEXT,
    applied_at TEXT,
    rolled_back_by TEXT,
    rolled_back_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### 3.3 Code-Capable Runtime 抽象接口

所有 Code-Capable Runtime（Codex / Claude Code）需实现以下能力：

| Capability | 描述 | 输入 | 输出 |
|:-----------|:-----|:-----|:-----|
| `code_plan` | 分析代码，生成自然语言修改方案 | problem_summary, 相关代码路径 | plan_summary, impact_scope, risk_level, expected_files |
| `code_patch` | 根据方案生成 patch | plan_summary, files | patch.diff, files_changed |
| `code_review` | 审阅已有 patch（预留，v0.9 不一定用） | patch.diff | review_summary, issues |
| `code_check` | 运行代码检查 | files | check_result |

**Adapter 注册方式**：

通过现有的 `runtime_registry` 表注册，新增 `codex` 和 `claude_code` runtime_type，capability discovery 返回上述能力列表。

```python
# 伪代码 — Code-Capable Runtime Adapter 接口
class CodeCapableAdapter:
    runtime_type: str  # "codex" | "claude_code"

    async def generate_plan(self, problem: str, context: dict) -> PlanResult:
        """分析代码 → plan_summary + impact_scope"""
        ...

    async def generate_patch(self, plan: dict, workspace: str) -> PatchResult:
        """生成 patch 到 staging 目录"""
        ...

    async def run_checks(self, patch_path: str, check_workspace: str) -> CheckResult:
        """在 isolated check_workspace 上运行 build/lint"""
        ...

    async def health_check(self) -> dict:
        """Runtime 是否可用"""
        ...
```

### 3.4 Staging + Isolated Check Workspace

```
.ai-company-os/staging/{request_id}/
  ├── plan_summary.md              # 自然语言方案（人类可读）
  ├── impact_summary.md            # 影响范围说明
  ├── patch.diff                   # 实际 git diff 格式的 patch
  ├── check_result.json            # 自动检查结果
  ├── protected_file_check.json    # { pre_check: {...}, post_check: {...} }
  ├── original_files/              # 原始文件副本（从真实项目目录复制）
  │   └── frontend/src/app/execution-requests/[id]/page.tsx
  ├── modified_files/              # 修改后文件副本（从 check_workspace 提取）
  │   └── frontend/src/app/execution-requests/[id]/page.tsx
  ├── check_workspace/             # ⭐ 隔离检查环境
  │   ├── .git/
  │   ├── frontend/
  │   ├── backend/
  │   └── ...                      # 整体项目副本 + 已应用 patch
  └── rollback_manifest.json       # 回滚清单 + 路径安全校验
      # {
      #   "files": [
      #     {"path": "frontend/src/app/.../page.tsx",
      #      "original": ".ai-company-os/staging/{id}/original_files/.../page.tsx",
      #      "staging": ".ai-company-os/staging/{id}/modified_files/.../page.tsx"}
      #   ],
      #   "created_at": "..."
      # }
```

**关键流程**：

```
1. plan_approved → patch 生成前
   → 复制 original_files/ 从真实项目目录
   → 调 Codex 生成 patch.diff（写入 staging 根目录）
   → patch_generated

2. checks 运行前
   → 将整个项目复制到 check_workspace/
   → 在 check_workspace/ 中应用 patch.diff
   → 在 check_workspace/ 中运行所有自动检查
   → 从 check_workspace/ 中提取变更文件 → modified_files/
   → 检查结果写入 check_result.json

3. founder_review
   → 真实项目目录未变
   → Founder 看到的是 check_workspace 中运行检查后的结果

4. Apply
   → modified_files/ → 真实项目目录（经过路径安全校验）
   → 写入 rollback_manifest.json

5. Rollback
   → original_files/ → 真实项目目录（经过路径安全校验）
```

**modified_files/ 生成方式（重点澄清）**：

```
✅ 正确方式：
真实项目目录 → 复制到 check_workspace → 在 check_workspace 中应用 patch
→ check_workspace 中变更的文件 → 复制到 modified_files/

❌ 错误方式：
不让 Codex 直接把文件写到真实目录再复制回来
不让 patch.diff 直接应用到真实目录
```

### 3.5 Protected Files 策略（双层检查）

**硬拦截列表** — 以下文件/文件模式默认不允许修改：

| 模式 | 原因 |
|:-----|:-----|
| `.env` | 敏感凭证 |
| `.env.*` | 所有环境变量文件 |
| `*.db` | SQLite 数据库文件 |
| `*secret*` | 密钥相关 |
| `*credential*` | 凭证相关 |
| `*token*` | Token 相关 |
| `*deploy*` | 部署配置 |
| `.git/config` + `.git/*` | Git 配置 |
| `docker-compose*.yml` | 部署编排 |
| `Dockerfile` | 镜像构建 |
| `*migration*` | 数据库迁移文件 |

**双层检查**：

```
Pre-check（patch 生成前）：
  扫描 files_expected_json
  如果触碰到 protected files → 阻止 Coding Agent 继续
  输出: protected_file_check_json.pre_check

Post-check（patch 生成后）⭐ 真正的安全闸门：
  扫描 patch.diff 中所有涉及的文件路径
  扫描 files_changed_json
  扫描 rollback_manifest_json 中所有路径
  如果任何一条路径触碰到 protected files → checks_failed
  输出: protected_file_check_json.post_check
  写入 protected_file_check_json 到 staging
```

**最终规则**：
- Pre-check 通过但 post-check 发现 protected files → `checks_failed`，不允许 apply
- Pre-check 和 post-check 都通过 → 允许继续
- Founder 界面显示：`"❌ 此修改涉及受保护文件（{文件名}），已被阻止"`

### 3.6 自动检查（L1，在 isolated check_workspace 中运行）

v0.9 至少做以下检查：

| 检查 | 命令 | 阻断性 | 运行位置 |
|:-----|:-----|:-------|:---------|
| 前端 build | `npm run build` 或 `next build` | **是** — build 失败不能 apply | check_workspace |
| 后端 import | `python -c "from app.main import app"` | **是** — 导入失败不能 apply | check_workspace |
| 后端路由 | `curl http://localhost:8001/docs` | **否** — warning，不阻塞 | check_workspace |
| TypeScript lint | `npx tsc --noEmit` | **是** — 类型错误不能 apply | check_workspace |

如果项目没有 TypeScript 或特定工具链，对应检查自动跳过（记为 `skipped`，不阻断）。

**checks_warning 处理**：
- 当所有阻断性检查通过但有非阻断性 warning 时 → `checks_warning`
- Apply 按钮默认显示灰色方案 + `"Apply with warning"` 文字
- 点击后弹确认对话框：`"⚠️ 自动检查存在 {N} 条 warning。你确认仍要应用吗？"`
- 确认后记录 `applied_with_warning = true`

### 3.7 Apply / Rollback 机制 + 路径安全校验

**Apply 流程**：

1. 读取 `rollback_manifest.json`
2. 对 manifest 中每条路径执行 **路径安全校验**：
   - 不能是绝对路径
   - 不能包含 `..` 或 `../`
   - 路径解析后必须在 repo root 内
   - 不能指向 `.git` 目录
   - 不能指向 protected files（再次确认）
3. 所有校验通过后，将 `modified_files/` 复制到实际项目目录
4. 更新 `code_change_requests.status = "applied"`
5. 更新关联 `execution_request.status = "verification_pending"`（⭐ 不直接 verified_success）
6. 更新 `improvement_proposal.status = "action_created"`（保持 v0.8 原则）

**Rollback 流程**：

1. 读取 `rollback_manifest.json`
2. 对 manifest 中每条路径执行 **相同的路径安全校验**
3. 所有校验通过后，将 `original_files/` 复制回实际项目目录
4. 更新 `code_change_requests.status = "rolled_back"`
5. 更新关联 `execution_request.status = "rolled_back"`（新增状态）

**路径安全校验函数**：

```python
def safe_path_join(repo_root: str, relative_path: str) -> str:
    """防止路径穿越攻击。
    
    规则：
    - relative_path 不能是绝对路径
    - relative_path 不能包含 ..
    - 合并后的路径必须在 repo_root 内
    - 不能指向 .git 目录
    - 不能匹配 protected file 模式
    """
    ...
```

### 3.8 Verification 闭环（与 v0.8 原则一致）

Apply 后不直接 verified_success。Founder 手动验证功能 OK 后：

```
code_change_request.applied
  → execution_request.status = verification_pending
  → proposal.status = action_created (保持)

Founder 打开页面/系统看效果，确认 OK：
  → 在 UI 上点击 "✅ 验证成功"
  → execution_request.status = verified_success
  → proposal.status = closed_success

Founder 确认失败：
  → 在 UI 上点击 "❌ 验证失败"（或先 Rollback）
  → execution_request.status = verified_failed
  → proposal.status = closed_failed
```

### 3.9 与 v0.6 Runtime Layer 的衔接

v0.6 已经注册了 `codex` 和 `claude_code` 作为 `enabled=0` 的 placeholder runtime。v0.9：

1. 新增 `code_capable` runtime_type（或扩展现有 runtime_type 的能力描述）
2. Codex Adapter 实现 `CodeCapableAdapter` 接口
3. Claude Code Adapter 仅实现 shape（health + capability discovery）
4. capability discovery 返回 `["code_plan", "code_patch", "code_check"]`
5. Execution bridge 根据 runtime.capabilities 决定是否能路由 code_change action
6. **Codex enabled 状态取决于 Sprint A0 验证结果**：
   - Codex CLI 可用 → enabled=1
   - Codex CLI 不可用 → enabled=0 + experimental + 不阻塞后端结构验收

### 3.10 与 v0.8 Execution Bridge 的衔接

v0.8 的 execution_request 表新增 `code_change_request_id` 字段（可选），指向关联的 code_change_request。

`execution_request.action_type = "code_change_request"` 时，执行流程变为：

```
execution_request created (code_change_request 同时创建)
  → 执行器检测到 action_type=code_change_request
  → 不执行 v0.8 的 safe action 逻辑
  → 转交给 code_change_requests 工作流
  → code_change 完成后
  → 回写 execution_request.status = verification_pending
  → Founder 手动验证后 → verified_success / verified_failed
  → 同步回 proposal
```

**v0.8 的 blocked action 定义更新**：`modify_code` 从 blocked 移动到 v0.9 safe actions。

---

## 四、验收标准

### 验收 1: Codex Runtime 注册 + Capability Discovery（取决于 A0）

**输入**: v0.9 启动后查询 runtimes

**结果**:
- ✅ `codex` runtime 已注册（enabled=1 或 enabled=experimental，取决于 A0 验证）
- ✅ capability discovery 返回 `["code_plan", "code_patch", "code_check"]`
- ✅ health_check 正常返回（online 或 experimental 降级）
- ✅ Claude Code runtime 已注册（experimental），capability 至少包含 `code_plan`
- ❌ Claude Code 不要求完整流程，不阻塞验收
- ❌ Codex CLI 不可用时不阻塞系统启动（runtime 标记 experimental/offline）

### 验收 2: 自然语言计划生成

**输入**: Founder 通过 UI 或 Improvement Proposal 发起一个代码修改请求：
> "修复 Execution Request 详情页 verified_success 后仍显示确认按钮的问题"

**结果**:
- ✅ `code_change_request` 已创建
- ✅ `plan_summary` 为非空自然语言文本（描述要改什么、为什么改、怎么改）
- ✅ `impact_scope_json` 列出影响范围和风险评级
- ✅ `files_expected_json` 列出预计修改的文件
- ✅ 状态: `plan_generated`
- ❌ 没有修改任何源码

### 验收 3: Founder Approve Plan → 生成 Patch 到 Staging

**输入**: Founder 在 UI 上点击 "Approved" 确认方案

**结果**:
- ✅ `original_files/` 已从真实项目目录复制到 staging
- ✅ `patch.diff` 包含实际代码变更（写入 staging 根目录，不改真实目录）
- ✅ `check_workspace/` 已创建并应用了 patch
- ✅ `modified_files/` 已从 check_workspace 提取
- ✅ `rollback_manifest.json` 已生成（路径安全校验通过）
- ✅ 状态: `patch_generated`
- ❌ 没有修改真实项目目录的任何文件

### 验收 4: 自动检查执行（在 isolated check_workspace 中）

**输入**: patch_generated → run checks

**结果**:
- ✅ 检查在 `check_workspace/` 中运行，不污染真实项目目录
- ✅ `check_result.json` 已写入（包含 build / lint / typecheck 结果）
- ✅ `protected_file_check.json` 已写入（包含 pre-check + post-check 结果）
- ✅ `checks_passed` 状态可正确流转
- ✅ `checks_failed` 状态阻止 apply

**额外验证**:
- ✅ Pre-check 通过但 post-check 发现 protected file → `checks_failed` → 阻止 apply
- ✅ Build 失败 → `checks_failed` → 阻止 apply
- ✅ Path traversal（../）在 manifest 中被拒绝 → apply/rollback 失败

### 验收 5: Founder Apply + Founder 手动验证（不直接 verified_success）

**输入**: checks_passed → Founder 在 UI 上点击 "Apply"

**结果**:
- ✅ 实际项目目录中的文件已被修改（modified_files → 项目目录，经过路径安全校验）
- ✅ `code_change_request.status = "applied"`
- ✅ 关联 `execution_request.status = "verification_pending"`（⭐ 不直接 verified_success）
- ✅ 关联 `improvement_proposal.status = "action_created"`（保持 open）

**输入**: applied → Founder 手动验证功能 OK → 点击 "✅ 验证成功"

**结果**:
- ✅ `execution_request.status = "verified_success"`
- ✅ `improvement_proposal.status = "closed_success"`

**输入**: applied → Founder 在 UI 上点击 "Rollback"

**结果**:
- ✅ 实际项目目录中的文件已被还原（original_files → 项目目录，经过路径安全校验）
- ✅ `status = "rolled_back"`
- ✅ 关联 `execution_request.status = "rolled_back"`（新增状态）

### 验收 6: Founder UI — 不审 Diff

**输入**: Founder 打开 code_change_request 详情页

**结果**:
- ✅ 显示自然语言方案摘要（非代码）
- ✅ 显示影响范围（文件数、组件名、功能区域）
- ✅ 显示风险评级
- ✅ 显示自动检查结果（✅/⚠️/❌ 图标 + 自然语言说明）
- ✅ 显示手动验证步骤
- ✅ Apply / Rollback / Reject 按钮
- ✅ `checks_warning` 时 Apply 按钮有 "Apply with warning" 标签 + 二次确认弹窗
- ✅ 不需要 Founder 看 diff 就能做决策（diff 作为折叠的审计材料）

### 验收 7: checks 在 isolated check_workspace 中运行

**输入**: checks 运行前检查真实项目目录没有被修改

**结果**:
- ✅ 所有检查命令在 `check_workspace/` 中执行
- ✅ 真实项目目录保持 patch 生成前的状态
- ✅ check_workspace 中已正确应用 patch.diff
- ✅ modified_files/ 来自 check_workspace 的变更文件

### 验收 8: Post-check protected file 失败阻止 apply

**输入**: 修改涉及 protected file（如 .env），但 files_expected 中未提及

**结果**:
- ✅ pre-check 通过（files_expected 不包含 .env）
- ✅ post-check 检测到 patch.diff 涉及 .env
- ✅ `checks_failed`，不允许 apply
- ✅ protected_file_check_json.post_check 记录了违规路径

### 验收 9: Path traversal 被拒绝

**输入**: rollback_manifest.json 中包含 `"../../.env"` 的路径

**结果**:
- ✅ `safe_path_join` 检测到路径穿越
- ✅ Apply / Rollback 拒绝执行，返回错误
- ✅ 不修改任何文件

### 验收 10: Apply 后进入 verification_pending

**输入**: Applied 完成

**结果**:
- ✅ `execution_request.status = "verification_pending"`
- ✅ `improvement_proposal.status` 保持 `action_created`（未 close）
- ✅ Founder 手动确认后 → `verified_success` / `closed_success`

### 验收 11: checks_warning 需要额外确认

**输入**: checks 结果包含 warning，不包含阻断性失败

**结果**:
- ✅ 状态: `checks_warning`
- ✅ Apply 按钮显示灰色方案 + `"Apply with warning"`
- ✅ 点击后弹确认对话
- ✅ 确认后 `applied_with_warning = true`
- ✅ 可以正常 apply

### 验收 12: Codex CLI 不可用不影响系统启动

**输入**: Codex CLI 未安装或 path 不可访问

**结果**:
- ✅ System 正常启动
- ✅ Codex runtime `enabled=0`，capability 仍可发现
- ✅ Founder UI 显示 Codex 离线
- ✅ 系统其余功能（v0.8 执行桥等）不受影响

---

## 五、执行计划

### Sprint A0 (~1h) — Code Runtime Capability Spike

| Step | 文件 | 说明 |
|:-----|:-----|:------|
| 0 | terminal | 检查 codex --version / claude --version |
| 1 | terminal | 测试非交互生成 plan / patch |
| 2 | terminal | 测试 workspace 限制能力 |
| 3 | terminal | 测试输出 patch/diff 格式 |
| 4 | terminal | 确认降级路径：不可用时用 mock adapter |
| 5 | 决策 | 根据结果决定 codex enabled=1 vs experimental |

### Sprint A (~3.5h) — Code-Capable Runtime 抽象 + Codex Adapter

| Step | 文件 | 说明 |
|:-----|:-----|:------|
| 1 | `backend/app/runtime/code_capable/__init__.py` | CodeCapableRuntime 抽象接口 |
| 2 | `backend/app/runtime/code_capable/base.py` | CodeCapableAdapter 基类（generate_plan / generate_patch / run_checks / health_check） |
| 3 | `backend/app/runtime/code_capable/codex_adapter.py` | Codex CLI 适配器（真实调用 codex CLI，或 mock 降级） |
| 4 | `backend/app/runtime/code_capable/claude_adapter.py` | Claude Code shape（health + capability，不跑完整流程） |
| 5 | `backend/app/runtime/routes.py` | 扩展 capability discovery API |
| 6 | `backend/app/models/runtime_registry.py` | seed 更新（codex enabled=取决于 A0, claude_code enabled=0 but discoverable） |
| 7 | 验证 | Codex health check + capability discovery |

### Sprint B (~4.5h) — code_change_requests 表 + 后端链路 + Staging

| Step | 文件 | 说明 |
|:-----|:-----|:------|
| 8 | `backend/app/models/code_change_request.py` | 模型 |
| 9 | `backend/app/models/__init__.py` | 注册模型 |
| 10 | `backend/app/routers/code_change_requests.py` | CRUD + 状态机路由 |
| 11 | `backend/app/code_bridge/__init__.py` | 包初始化 |
| 12 | `backend/app/code_bridge/planner.py` | plan 生成逻辑（调 Codex generate_plan） |
| 13 | `backend/app/code_bridge/patch_generator.py` | patch 生成 + staging 写入 + check_workspace 创建 |
| 14 | `backend/app/code_bridge/checks_runner.py` | 自动检查（在 check_workspace 中运行） |
| 15 | `backend/app/code_bridge/protected_files.py` | Protected files 双层检查策略 |
| 16 | `backend/app/code_bridge/applier.py` | Apply + Path safety + Rollback |
| 17 | `backend/app/routers/execution_requests.py` | 扩展 action_type=code_change_request 路由 |
| 18 | `backend/app/execution_bridge/policy.py` | 更新 blocked actions（modify_code 移至 v0.9 白名单） |
| 19 | 验证 | Plan → Patch → Checks → Apply → Rollback 全链路 |

### Sprint C (~2.5h) — 前端 + Protected Files + Rollback

| Step | 文件 | 说明 |
|:-----|:-----|:------|
| 20 | `frontend/src/types/code_change.ts` | TypeScript 类型 |
| 21 | `frontend/src/lib/api.ts` | API 函数 |
| 22 | `frontend/src/app/code-change-requests/page.tsx` | 列表页 |
| 23 | `frontend/src/app/code-change-requests/[id]/page.tsx` | 详情页（摘要展示、确认、apply/rollback、二次确认） |
| 24 | `frontend/src/app/layout.tsx` | 导航链接 |
| 25 | 验证 | 验收 1-12 完整测试 |
| 26 | Commit + Tag + GitHub Release | v0.9 |

---

## 六、路线衔接

| 版本 | 核心 | 与 v0.9 的关系 |
|:-----|:-----|:----------------|
| v0.7 | Improvement Proposal Layer | 代码修改请求的来源之一 |
| v0.8 | Controlled Execution Bridge | 执行总入口，v0.9 扩展 action_type |
| **v0.9** | **Code-Capable Runtime Bridge** | **让代码修改进入受控执行流程** |
| v0.9.1 | GitHub PR / Merge / Deploy | 从 staging 到推送 |
| v1.0 | Agent Meeting Session | 多 Agent 会议 + 决策产出到执行桥 |

---

> **相关文档**
> - Roadmap: `docs/AI-COMPANY-OS-ROADMAP.md`
> - v0.8 Controlled Execution Bridge MVP PRD: `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.8-CONTROLLED-EXECUTION-BRIDGE-MVP-PRD.md`
> - v0.6 Runtime Layer MVP PRD: `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.6-RUNTIME-LAYER-MVP-PRD.md`
> - 长期宪法: `docs/AI-COMPANY-OS-CONSTITUTION.md`
