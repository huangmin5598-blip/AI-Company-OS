---
title: "Company Instance Config — AI Company OS Core vs Instance 边界文档"
domain: configuration
---

# Company Instance Config

> **版本**：v0.28 · 2026-05-17  
> **用途**：明确 OS Core 与 Company Instance 的边界，指导配置分离

---

## 1. 为什么需要分离

AI Company OS 启动时是一个单实例系统——codebase、config、runtime 全在一起。为了让系统可复用、可产品化，需要明确：

- 什么是**所有人都共享的**（OS Core）
- 什么是**每个公司独有的**（Company Instance）

---

## 2. 边界划分

### OS Core 管什么（提交到 repo，保持不变）

| 层 | 管理内容 | 文件位置 |
|:---|:---------|:---------|
| **Execution Spine** | Work Order 生命周期、状态机、执行模式 | `backend/app/models/work_order.py`, `backend/app/services/work_order_executor.py` |
| **Governance Kernel** | Capability Boundary 动作分类、审批规则 | `config/capability-boundary.yaml`, `config/safe-output-policy.yaml` |
| **Memory & Asset** | Run Ledger Schema、Asset Registry Schema、Cost Summary | `backend/app/models/run_ledger_event.py`, `backend/app/models/asset_record.py` |
| **Founder Control** | Founder Console 逻辑、CEO Cmd 框架 | `backend/app/routers/founder_console.py`, `scripts/ceo_cmd.py` |
| **Evidence Layer** | Evidence Dashboard 模板、Sanitize 规则 | `backend/app/services/evidence_summary_service.py` |
| **Manifests** | Runtime 声明、Capability 声明、Safe Output 规则 | `config/runtime-manifest.yaml`, `config/capability-manifest.yaml` |

### Company Instance 管什么（实例配置，不入 repo）

| 配置项 | 说明 | 文件字段 |
|:-------|:------|:---------|
| **公司标识** | 公司名称、创始人名称、版本号 | `company.*` |
| **显示配置** | 语言、时区、公开证据开关 | `display.*` |
| **运行时选择** | 启用哪些 runtime（引用 runtime-manifest） | `runtimes[].enabled` |
| **业务线** | 公司业务领域定义 | `business_lines[]` |
| **定时任务** | 覆盖默认的定时任务配置 | `schedules[]` |
| **通知渠道** | 通知发送目标 | `notification_channels[]` |
| **审批策略** | 审批默认行为 | `approval_policy.*` |

---

## 3. 文件架构

```
config/
├── company-instance.example.yaml    ← 实例配置模板（PLATFORM，可提交）
├── company-instance.yaml            ← 真实实例配置（.gitignore，不入库）
├── runtime-manifest.yaml            ← 运行时声明（PRODUCT，共享）
├── capability-manifest.yaml         ← 能力声明（PRODUCT，共享）
├── safe-output-policy.yaml          ← 安全输出策略（PRODUCT，共享）
├── capability-boundary.yaml         ← 动作边界规则（PRODUCT，共享）
└── skill_registry.yaml              ← 技术路由规则（PRODUCT，共享）
```

---

## 4. 初始化流程

```
1. Runtime Manifest → 声明可用的运行时
2. Capability Manifest → 声明可用的 actor 与能力
3. Company Instance → 选择启用的运行时 + 业务线 + 调度 + 通知 + 审批
4. OS Core → 读取所有配置，初始化运行时、注册能力、加载调度
```

**当前状态**：Manifest 已定义，但 OS Core 尚未自动读取。运行时初始化仍通过 seed 脚本完成。自动读取将在 v0.29+ 实现。

---

## 5. 不变性规则

### OS Core 不变性

- ✅ 无硬编码公司名称/创始人名称
- ✅ 无硬编码运行时 endpoint（来自 manifest）
- ✅ 无硬编码业务线名称
- ✅ 所有公司特有参数来自 `company-instance.yaml`

### Company Instance 规则

- ✅ 真实配置文件（`company-instance.yaml`）在 `.gitignore` 中
- ✅ 模板文件（`company-instance.example.yaml`）可提交
- ✅ 实例不包含运行时 adapter 逻辑
- ✅ 实例不包含治理规则

---

## 6. 迁移状态

| 组件 | 状态 | 计划 |
|:-----|:------|:------|
| Company Instance 定义 | ✅ v0.28 完成 | 引用已存在 |
| Runtime Manifest | ✅ v0.28 完成 | 手动声明 |
| Capability Manifest | 🔮 Sprint B | v0.28 内完成 |
| Safe Output Policy | 🔮 Sprint C | v0.28 内完成 |
| OS Core 自动读取配置 | 🔮 v0.29+ | 后续版本 |

---

## 7. 当前限制

- OS Core 尚未实现自动读取 `company-instance.yaml`（运行时初始化通过 seed 脚本）
- Manifest 验证通过 `scripts/manifest_validator.py` 手动执行，非自动拦截
- 多实例（多 Company Instance）尚不支持
- 配置变更不自动热加载，需重启
