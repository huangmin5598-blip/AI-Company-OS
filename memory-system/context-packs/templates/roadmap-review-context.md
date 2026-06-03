# Context Pack Template — Roadmap Review
# v0.46.1 — 新增：Roadmap 审查默认上下文包模板
# 规则：任何 roadmap 修订/审查必须引用 SA-002 + 当前 roadmap

## 任务类型
roadmap_review

## View A 经营阶段
- learning_iteration
- readiness_execution

## View B 技术层
- founder_control_plane
- governance_kernel
- company_memory_context_layer
- product_line_workspace

## 包含的 Memory 类型
- system_architecture
- founder_decision
- governance_rule
- runtime_lifecycle
- product_line_learning

## 排除的 Sensitivity
- L3+
- L4

## 默认 Token Budget
2500

## Required Core Memory
- **MEM-20260603-SA-002** — AI Company OS 七层架构与 P0/P1/P2 成熟度路线（必须引用）

## 使用说明
1. **强制引用 SA-002** 的 summary + selected_context
2. 扫描 approved/ 下匹配的 memory
3. 按 view_a_stage 和 view_b_layer 匹配当前 roadmap 涉及的范围
4. 按 priority 排序，token budget 内取 top N
5. 取 summary 和 selected_context（非全文）
6. 生成 Context Pack 写入 private/memory/context-packs/generated/

## Roadmap 审查检查项

在 roadmap 审查中必须回答：

1. **P0/P1/P2 对齐：** 计划中的每项工作在 P0/P1/P2 矩阵中是否正确定位？
2. **缺口驱动：** 路线是否由产品线运行缺口驱动，而非技术好奇心？
3. **一次一层：** 是否有跳层行为？（比如 Memory P0 未完成就做自动 dispatch）
4. **三服务验证：**
   - [ ] 是否增强真实产品线运行？
   - [ ] 是否形成可复用 OS 能力？
   - [ ] 是否新增公司资产沉淀？
5. **Memory 关联：** roadmap 变更是否需要生成新的 memory candidate？
6. **平行文档检查：** 新增内容是否能与已有架构文档合并，而非另起炉灶？
