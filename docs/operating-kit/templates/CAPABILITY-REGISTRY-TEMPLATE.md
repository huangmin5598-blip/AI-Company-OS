---
title: "Capability Registry Template — AI Company OS 能力注册模板"
domain: operating-kit
---

# Capability Registry Template

> **用途**：注册一个新的 Agent / Runtime / Capability 到 AI Company OS 能力地图。  
> **关联文件**：`config/capability-registry.yaml`（完整注册表）、`config/capability-manifest.yaml`（轻量声明）  
> **前置条件**：Agent 已在对应 Runtime 中正常运行。

---

## 1. 选择注册层

- [ ] **Layer 1 — Founder-facing Agent**：直接与 Founder 交互，高权限
- [ ] **Layer 2 — System Command Interface**：CLI / API 接口
- [ ] **Layer 3 — Specialist Agent**：特定领域执行者
- [ ] **Layer 4 — Runtime / Platform**：模型网关、后台执行器
- [ ] **Automation**：定时自动化任务
- [ ] **Administration**：受信管理员角色

---

## 2. Agent 基本信息

| 字段 | 填写 |
|:-----|:------|
| Agent ID | ` ` |
| Display Name | ` ` |
| Role Description | ` ` |
| Runtime | `hermes / openclaw / codex / claude_code / system` |
| Risk Level | `low / medium / high / critical` |
| Cost Class | `cheap / moderate / expensive` |
| Quality Class | `draft / standard / premium` |
| Default Output Contract | ` ` |

---

## 3. 能力声明

列出该 Agent 具备的能力（每行一个）：

```
- capability_1: <简短描述>
- capability_2: <简短描述>
- ...
```

**能力命名规范**：`snake_case`，动词开头，如 `web_research`、`code_generation`、`status_query`

---

## 4. 边界声明

该 Agent **不能**做什么：

```
- cannot <action_1>
- cannot <action_2>
- ...
```

---

## 5. 需要 Founder 审批的动作

```
- <action_1>
- <action_2>
- ...
```

---

## 6. 关联信息

| 字段 | 填写 |
|:-----|:------|
| Supported Workflows | ` ` |
| Supported Projects | ` ` |
| Related Skills (from skill_registry.yaml) | ` ` |
| Related Protocols | `MCP / ACP / HTTP / stdio` |
| Boundary Profile | `founder_facing_agent / system_command_interface / specialist_agent / developer_agent / runtime_platform / automation / system_api / administration` |

---

## 7. Manifest 更新清单

注册完成后，确认以下文件已更新：

- [ ] `config/capability-registry.yaml` — 添加完整 agent 记录
- [ ] `config/capability-manifest.yaml` — 添加轻量 actor 声明
- [ ] `config/runtime-manifest.yaml`（如新增 runtime）— 添加 runtime 声明
- [ ] `docs/registry/CAPABILITY-REGISTRY.md` — 更新人读版文档
- [ ] `docs/registry/CAPABILITY-MANIFEST.md` — 更新人读版文档
- [ ] 运行 `python3 scripts/manifest_validator.py validate` — 确认交叉引用正确

---

_document_status: template_
