# Code Bridge 默认策略 — V0.9.1.1

> 更新时间：2026-05-24 (v0.9.1.1 修订)
> 
> **核心原则：Codex = Planner / Reviewer，Hermes = Deterministic Applier，Git Diff = Evidence，Founder = Final Verifier**

---

## 一、为什么是这个策略

v0.9 和 v0.9.1 的实战运行暴露了两个问题：

1. **Codex Patch 模式不稳定** — `codex exec` 生成完整代码 diff 的任务会在 34 分钟后卡死退出，无法可靠产出可直接应用的 patch
2. **Codex Plan 模式稳定** — `codex exec` 只读分析、输出结构化文本（PLAN_SUMMARY/IMPACT/RISK/FILES）的任务在 ~40-70s 内稳定完成

基于这个观察，默认工作流设计为：

```
Codex 负责「想清楚要改什么」→ 输出 Plan
Hermes 负责「精确地改」→ 用 patch 工具做 deterministic apply
Git diff 负责「证据」→ 记录实际改动
Founder 负责「最终确认」→ approve / rollback
```

---

## 二、默认工作流

```mermaid
flowchart LR
    A[Problem / PRD] --> B[Codex: Generate Plan]
    B --> C{Plan Approved?}
    C -->|Yes| D[Hermes: Deterministic Apply]
    C -->|No| B
    D --> E[Git Diff: Capture Evidence]
    E --> F[Run Checks]
    F --> G{Checks Passed?}
    G -->|Yes| H[Founder Review]
    G -->|Warning| H
    G -->|Failed| D
    H --> I{Approved?}
    I -->|Yes| J[Apply (write to workspace)]
    I -->|No| B
    J --> K[Git Diff: Final Evidence]
    K --> L[Release Notes]
```

### 步骤详情

| 步骤 | 负责方 | 输出 | 预期耗时 |
|:----|:-------|:-----|:--------|
| 1. Generate Plan | Codex CLI | PLAN_SUMMARY + IMPACT + RISK + FILES | 40-70s |
| 2. Approve Plan | Founder | status=plan_approved | 即时 |
| 3. Apply Changes | Hermes (patch tool) | 精确的 find-and-replace edits | 秒级 |
| 4. Capture Diff | Git | git diff → 补丁文件 | 即时 |
| 5. Run Checks | Hermes (terminal) | npm run build / tsc 结果 | 30s-2min |
| 6. Review + Apply | Founder | apply / rollback 决策 | 即时 |
| 7. Evidence | Hermes | release notes + screenshots | 即时 |

---

## 三、Plan 输出格式

Codex Plan 调用使用的 prompt 模板（位于 `codex_adapter.py` 的 `generate_plan` 方法中）：

```
Read the relevant files in this repository.
Problem: {problem}

Output exactly in this format:
PLAN_SUMMARY: (1-3 sentences describing what to change and how)
IMPACT: (which components/services are affected, risk assessment)
RISK: low/medium/high
FILES: (comma-separated list of file paths to modify)

Do NOT modify any files. Only read and analyze.
```

### Plan 解析

解析函数位于 `codex_adapter.py`：

| 字段 | 提取方式 | 回退策略 |
|:-----|:---------|:--------|
| `plan_summary` | `_extract_section(output, "PLAN_SUMMARY")` | `_clean_output(output)[:500]` |
| `impact_scope` | `_extract_section(output, "IMPACT")` | risk_level |
| `risk_level` | `_extract_risk(output)`（关键字匹配） | "medium" |
| `files_expected` | `_extract_files(output)`（FILES 段落 + 反引号回退） | [] |

---

## 四、Patch 策略（两个路径）

### 路径 A：Hermes Deterministic Apply（默认 ✅）

直接使用 `patch` 工具对文件做精确的 find-and-replace 修改。

**适用场景**：所有生产环境修改

**优点**：确定性强、可回滚、不依赖 Codex 的代码生成稳定性

**命令模式**：
```python
patch(path=file_path, old_string=..., new_string=...)
# 或
write_file(path=file_path, content=full_content)  # 仅限小文件整体替换
```

### 路径 B：Codex Patch + `--output-schema`（推荐实验路径 ✅）

使用 `codex exec` 的 `--output-schema <schema.json>` 生成**结构化 JSON + 完整 git diff**。

**适用场景**：复杂重构、大量文件修改、Hermes Apply 逐个 patch 效率低时

**当前状态**：✅ **v0.9.1.1 验证通过**

#### 实验结论（Task 4，2026-05-24）

通过 `codex exec` + `--output-schema` 在 ai-company-os 仓库上的实测：

| 项目 | 结果 |
|:-----|:-----|
| schema 有效性 | ✅ `--output-schema` 支持 JSON Schema draft-07 |
| 输出格式 | ✅ 纯 JSON，无 markdown 包裹，无系统文本 |
| 嵌套对象 | ✅ `files[].path` + `files[].change` 正常工作 |
| enum 约束 | ✅ `risk: low/medium/high` 被正确执行 |
| `additionalProperties: false` | ✅ 严格模式生效 |
| **git diff 有效性** | ✅ **`git apply --check` 通过**，diff 直接可 apply |
| diff 生成耗时 | ~20-30s（小型改动） |
| 可回滚 | ✅ `git checkout -- .` 干净回滚 |

**关键约束**（OpenAI structured output API 要求）：
- `required` 数组必须包含**所有** `properties` 中的 key
- 所有 properties 都必须标记为 required
- `additionalProperties: false` 建议加上以避免意外字段

#### 推荐 JSON Schema 模板

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["plan_summary", "risk", "impact", "files", "diff"],
  "additionalProperties": false,
  "properties": {
    "plan_summary": { "type": "string", "description": "1-3 sentences describing what to change and how" },
    "risk": { "type": "string", "enum": ["low", "medium", "high"] },
    "impact": { "type": "string", "description": "Affected components/services" },
    "files": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "change"],
        "additionalProperties": false,
        "properties": {
          "path": { "type": "string" },
          "change": { "type": "string", "description": "What to change in this file" }
        }
      }
    },
    "diff": { "type": "string", "description": "Complete git diff in unified format" }
  }
}
```

#### 使用方式

```bash
# Step 1: Codex 生成结构化 Plan + Diff
codex exec "add feature X..." \
  --dangerously-bypass-approvals-and-sandbox \
  --output-schema /path/to/patch_spec_schema.json \
  --output-last-message /tmp/patch_spec.json

# Step 2: 解析 JSON 并验证 diff
cat /tmp/patch_spec.json | jq '.diff' > /tmp/change.diff
git apply --check /tmp/change.diff   # 验证
git apply /tmp/change.diff           # 应用

# Step 3: 回滚（如需要）
git checkout -- <files>
```

**⚠️ 注意**：`--output-schema` 仅用于**生成** patch_spec JSON，不用于**应用**。应用侧仍用 `git apply` 做确定性操作。

---

## 五、异步 Job 模型

> 新增于 v0.9.1.1

为了避免 HTTP 请求生命周期承载 40-90 秒的 Codex 调用，新增 `code_runtime_jobs` 表 + 异步 job API。

**API**：
```
POST   /api/v1/code-runtime-jobs          → 返回 { job_id, status: "queued" }
GET    /api/v1/code-runtime-jobs/{id}     → 返回 { status, result_text, elapsed_seconds, ... }
POST   /api/v1/code-runtime-jobs/{id}/retry → 重置 failed job 为 queued
```

**执行模型**：`threading.Thread` + 独立事件循环。子进程 I/O 全部走文件（`~/.ai-company-os/codex-runs/{run_id}/`），无 pipe 死锁风险。

**状态机**：`queued → running → success / failed / timeout`

---

## 六、安全边界

### 子进程防护（`_run_codex`）

```
stdin=DEVNULL              # 防止等待输入
stdout/stderr → 文件        # 避免 pipe 缓冲区填满
start_new_session=True      # 进程组隔离
explicit env                # PATH / HOME / CODE_RUNTIME
subprocess.run(timeout=...) # 超时触发 TimeoutExpired
os.killpg()                 # 超时后杀死整个进程组
```

### 文件防护

```
protected_file_check_json   # 修改前检查 protected files
14 protected file patterns  # .env, *.db, config/*, 等
pre-check + post-check      # 修改前后双重校验
```

---

## 七、Rollback 策略

每次 apply 前的 git diff 保留为补丁文件：

```bash
git diff > /tmp/v{version}-patch.diff
git checkout -- <files>    # rollback
git apply <patch.diff>     # re-apply
```

已验证可正常 rollback → re-apply 全链路。详见 v0.9.1 实战记录。
