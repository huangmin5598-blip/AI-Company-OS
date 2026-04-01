# OS Capability Project Pool

**Version**: 1.1 (With Layered Ownership)
**Created**: 2026-04-01
**Updated**: 2026-04-01
**Owner**: CEO (main)

---

## 一、Ownership Structure (Layered)

| Layer | Role | Responsibility |
|-------|------|----------------|
| **Line Owner** | CEO (main) | Owns the entire OS capability building line |
| **Project Owner** | lead-os | Drives OS projects, tracks progress, ensures continuity |
| **Executor** | tiger-coder (specific agent) | Executes specific implementation tasks |

**Why this layering:**

- CEO owns the line → won't let OS capability line be swallowed by real projects
- lead-os drives projects → won't let projects "naturally disappear" after P0
- tiger-coder executes → handles specific implementation

---

## 二、Current OS Capability Projects

### P0 Projects (4-8 Week Priority)

| # | Project | Line Owner | Project Owner | Executor | Stage | Next Stage | Operational Status | Freeze Rule | End State |
|---|---------|-----------|---------------|----------|-------|------------|-------------------|-------------|-----------|
| 1 | **run-ledger-v1** | main | lead-os | tiger-coder | P0 | P1 | In Progress | Complete P1 before freeze | Unified run event schema, SQLite storage, timeline query |
| 2 | **policy-approval-center-v1** | main | lead-os | tiger-coder | P0 | P1 | Planning | Complete P1 before freeze | Permission enforcement, approval workflow, policy layer |
| 3 | **skill-pack-runtime-v1** | main | lead-os | tiger-coder | P0 | P1 | Planning | Complete P1 before freeze | Skill/Subagent/Team三层结构, research-agent试点 |
| 4 | **execution-workspace-v1** | main | lead-os | tiger-coder | P0 | P1 | Planning | Complete P1 before freeze | Run/task→workspace→branch/sandbox, control-center P1接入 |

### Existing Projects (Evolution Mapping)

| # | Project | Line Owner | Project Owner | Executor | Stage | Next Stage | Operational Status | Freeze Rule | End State | 映射方向 |
|---|---------|-----------|---------------|----------|-------|------------|-------------------|-------------|-----------|---------|
| 5 | **gateway-lite-v1** | main | lead-os | tiger-coder | MVP | P1 | Running | Complete P1 before freeze | Cost governance, fallback tracking | → Policy & Approval Center |
| 6 | **control-center-v1** | main | lead-os | tiger-coder | P1 | P2 | In Progress | Complete P2 before freeze | 7 modules operational, iterate on control plane | → Execution Control Plane |
| 7 | **capability-registry-v1** | main | lead-os | tiger-coder | P0 | P1 | Stable Running | Maintain before upgrade | Complete Agent/Project map, keep referenced | → Skill Pack Runtime |
| 8 | **routing-layer-v1** | main | lead-os | tiger-coder | P0 | P1 | In Progress | Complete P1 before freeze | Semantic routing rules layer | 升级为Execution Router |
| 9 | **checkpoint-resume-v1** | main | lead-os | tiger-coder | P0 | P1 | In Progress | Complete P1 before freeze | Resume from checkpoint | 扩展为Run+Worker Resume |
| 10 | **preflight-diagnostics-v1** | main | lead-os | lead-os | P0 | P1 | In Progress | Complete P1 before freeze | Pre-task health checks (5 items) | 继续 |
| 11 | **evidence-dashboard-lite-v1** | main | lead-os | tiger-coder | P1 | P2 | In Progress | Complete P2 before freeze | Update mechanism + display optimization | 继续 |

---

## 二、Run Ledger / Event Bus (P0 Priority)

### 为什么是最高优先级

- OS Core Infra，后续所有模块依赖它
- gateway, routing, checkpoint, workspace, policy, memory, control-center 都会写和读
- 没有统一事件层，其他能力都会散

### V1 目标 (Week 1-2)

- 定义 run event schema v1
- SQLite 存储：event_log (append-only) + run_state (快照)
- gateway-lite-v1 作为第一批 producer
- 支持 run timeline 查询/查看

### V1 Schema (核心字段)

```json
{
  "run_id": "唯一标识",
  "thread_id": "线程标识",
  "project_id": "项目标识",
  "task_id": "任务标识",
  "agent_id": "执行agent",
  "capability_id": "调用能力",
  "status": "created/running/completed/failed/blocked/skipped",
  "cost": "花费",
  "latency": "延迟",
  "artifacts": "产出物",
  "approvals": "审批记录",
  "interrupts": "中断记录",
  "resume_points": "恢复点",
  "escalation": "升级记录",
  "errors": "错误信息"
}
```

### 验收标准

- 一个 run 有统一 run_id
- 关键事件能写入 ledger
- 能按 run 查询事件时间线
- control-center-v1 可接入此时间线

---

## 三、Policy & Approval Center (P0)

### 目标

把权限、审批、白名单从 prompt 中剥离，变成正式治理层

### 范围

- tool permission
- write permission
- environment boundary
- approval rules
- sensitive operation approval
- outbound data policy

### V1 审批流

```
自动规则 → lead-os → CEO escalation
```

### 范围限制 (V1)

- skipped/blocked/escalation 需要审批
- 高风险 outbound/write/publish 需要审批

---

## 四、Skill Pack Runtime (P0)

### 目标

把 capability-registry-v1 升级成可运行的 Skill Pack 系统

### 三层结构

1. **Skill Pack Registry** - 可复用能力包
2. **Subagent Catalog** - 隔离执行者
3. **Team Topology** - 并行/协作模式

### 首试点

**research-agent** - 输入输出清晰，artifact 更好验收

### 每个 Skill 包含

- manifest
- SKILL.md
- trigger rules
- required inputs
- outputs
- artifacts
- success criteria
- fallback
- cost profile
- eval hooks

---

## 五、Execution Workspace + control-center-v1 P1

### Execution Workspace

- 独立执行层
- Run/Task → Workspace → Branch/Sandbox/Artifacts/Reviewer
- 隔离方案：
  - 默认：独立目录 + run/artifact/memory scope
  - 代码任务：Git branch/worktree
  - Docker：P1

### control-center-v1 P1

- 观察和操作 Execution Workspace
- 新增：run timeline, approval, review loop
- 不只是 UI 页面，是工作发生的地方

---

## 三、Role Responsibilities

### Line Owner (CEO / main)

-owns the entire OS capability building line
- decides which OS projects enter project pool
- decides upgrade / freeze / prioritize
- hosts Weekly OS Review and makes final decisions
- ensures OS line has resources and doesn't get swallowed by business projects

### Project Owner (lead-os)

- drives each OS project forward
- tracks: current_stage, next_stage, blockers, operational_status
- prevents projects from "naturally disappearing" after P0
- organizes Weekly OS Review materials
- summarizes blockers and forms upgrade/freeze recommendations
- coordinates OS Radar / Skills Gap inputs into project pool

### Executor (tiger-coder / specific agent)

- executes specific implementation tasks
- reports progress to project_owner
- doesn't decide on project stage transitions

---

## 四、Project Status Definitions

### roadmap_stage

| Stage | Description |
|-------|-------------|
| P0 | MVP / Proof of concept - Core functionality built |
| P1 | Iteration / Enhancement - Add features, stabilize |
| P2 | Production - Ready for production use |
| P3 | Maintenance - Long-term maintenance mode |

### operational_status

| Status | Description |
|--------|-------------|
| Planning | Project being planned |
| In Progress | Actively being built |
| Completed | Core functionality done |
| Running | In production use |
| Paused | Temporarily halted |
| Frozen | No longer actively developed |
| Cancelled | Stopped with reasons documented |

### freeze_rule

- Projects must complete P1 before being frozen
- Frozen projects must document reason
- No project should "naturally disappear" after P0

---

## 五、routing-layer-v1 Direction

**Approach**: Borrow base layer + build semantic rules

### Reuse from OpenClaw

- Gateway event ingestion
- WebSocket / RPC communication
- Agent status display
- Routing & health event frontend

### AI Company OS Focus (Own)

- Founder input / project input / system input classification
- Route type / route reason / next agent / escalation to semantics
- Timeout → resume / fallback / main_rescue rules
- Memory Layer / Registry / Evidence Layer integration
- Capability Registry / Project Flow rules

---

## 六、Weekly OS Review

### Review Frequency

- **Every Sunday 20:00** (or first working day)
- Separate from normal project review

### Review Checklist

1. Which OS projects are in P0 / P1 / P2?
2. Which projects have entered stable running?
3. Which projects are blocked?
4. Which projects need upgrade?
5. Which projects should be frozen?
6. Which need OS Radar / Skills Gap Review input?
7. Which projects completed P0 but have no next step?

### Weekly Output

- OS Progress Summary
- Project Status Table
- Blockers
- Upgrade / Freeze Decision Recommendations

---

## 七、Project Lifecycle Rules

### After P0 Completion

Every project must move to one of:

1. **Stable Running** - In production, working as expected
2. **Upgrade to P1** - Continue iteration
3. **Frozen** - Documented reason required

**Prohibited**: "Complete minimum version, then naturally disappear"

### Decision Authority

- Line Owner (CEO) makes final decision on upgrade / freeze
- Project Owner (lead-os) prepares recommendations and materials

---

## 八、CEO Decision Records (2026-04-01)

### Decision 1: control-center-v1 → Upgrade to P1

**Reason**:
- P0 complete with 7 modules
- Information layer skeleton formed
- Ready for stronger control plane evolution

### Decision 2: capability-registry-v1 → Stable Running

**Reason**:
- First version capability map complete
- Focus on ongoing maintenance and real references
- Don't upgrade for the sake of upgrading

**Requirements**:
- Continue maintained by lead-os
- Keep referenced in Skills Gap Review, project allocation, control-center

### Decision 3: evidence-dashboard-lite-v1 → Upgrade to P1

**Reason**:
- 5 external files completed and pushed to GitHub
- Already important part of external evidence layer
- Next: update mechanism + display optimization + external linkage

### Decision 4: routing-layer-v1 → Start Design

**Approach**: Borrow base layer + build semantic layer

**Execution**:
- Don't build routing capability from scratch
- Reference ClawManager Multi-Agent Routing for routing & control logic
- Continue compatible with OpenClaw Gateway for control plane
- Reference OpenClaw Office for status display & visualization
- tiger-coder starts designing AI Company OS semantic/rule/interface layer

**Focus** (AI Company OS owns):
- founder_input / project_input / system_input
- route_type / route_reason / next_agent / escalation_to
- timeout → resume / fallback / main_rescue
- Memory Layer / Registry / Evidence Layer integration
- Capability Registry / Project Flow rules

### Decision 5: preflight-diagnostics-v1 → Start P0

**Scope** (Minimum):
- Registry writable
- Memory Layer writable
- Gateway reachable
- Export path writable
- Key model / Ollama status normal

**Approach**: Minimum viable, not comprehensive

---

## 九、Next Steps

1. ✅ Layered ownership structure confirmed
2. ✅ lead-os takes ownership of project tracking
3. ✅ First round status maintenance completed
4. ✅ CEO decisions recorded
5. ⏳ lead-os continues tracking implementation

---

## Registry

| Field | Value |
|-------|-------|
| current_version | 1.1 |
| last_updated | 2026-04-01 |
| line_owner | main (CEO) |
| project_owner | lead-os |
| executor | tiger-coder |

---

*This document is the authoritative source for OS capability project tracking.*