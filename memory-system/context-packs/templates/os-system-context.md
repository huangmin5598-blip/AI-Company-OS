# Context Pack Template — OS System Layer Task
# v0.46.1 — 新增：任何 OS 系统层任务的默认上下文包模板
# 规则：所有 OS 系统层任务默认必须引用 SA-002

## 任务类型
os_system_task

## View A 经营阶段
- learning_iteration

## View B 技术层
- company_memory_context_layer
- governance_kernel
- workflow_skill_layer

## 包含的 Memory 类型
- system_architecture
- governance_rule
- runtime_lifecycle
- asset_evidence

## 排除的 Sensitivity
- L3+
- L4

## 默认 Token Budget
2000

## Required Core Memory
- **MEM-20260603-SA-002** — AI Company OS 七层架构与 P0/P1/P2 成熟度路线（任何 OS 系统层任务必须引用）

## 使用说明
1. **强制引用 SA-002** — 任何 OS 系统层任务的第一步都是加载 SA-002 的 summary + selected_context
2. 扫描 approved/ 下匹配的 memory，按 priority (core > normal > reference) 排序
3. 取每条 memory 的 summary 和 selected_context（非全文）
4. 在 token budget 内取 top N
5. 生成 Context Pack 写入 private/memory/context-packs/generated/

## 启动前检查项（对应 SA-002 三问框架）

在执行任何 OS 系统层任务前，必须回答：

1. **A 视角定位：** 本任务属于经营闭环哪一段？
   - opportunity_discovery / productization / build_production / growth_distribution / customer_interaction_sales / readiness_execution / learning_iteration

2. **B 视角定位：** 本任务属于 OS 技术支撑哪一层？
   - founder_control_plane / governance_kernel / company_memory_context_layer / asset_evidence_registry / workflow_skill_layer / runtime_adapter_layer / product_line_workspace

3. **P0/P1/P2 判断：** 当前做的是哪一级？是否提前做了 P2？

4. **三服务验证（必须同时满足）：**
   - [ ] 是否增强真实产品线运行？
   - [ ] 是否形成可复用 OS 能力？
   - [ ] 是否新增公司资产沉淀？

5. **Memory 关联：** 完成后是否需要生成新的 memory candidate？

## 提醒
- 如果任务涉及架构变更，应改用 `architecture-review-context.md`
- 如果任务涉及路线规划，应同时引用 `roadmap-review-context.md`
- 如果是产品线内任务，应使用产品线专用 context pack
