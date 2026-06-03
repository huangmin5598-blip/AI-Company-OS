# Context Pack Template — Architecture Review
# v0.46 P0 — 选择规则模板，不写入具体 memory 引用
# v0.46.1 — 新增 SA-002 必引规则 + 三问判断框架

## 任务类型
architecture_review

## View A 经营阶段
- readiness_execution
- learning_iteration

## View B 技术层
- company_memory_context_layer
- governance_kernel

## 包含的 Memory 类型
- system_architecture
- governance_rule
- runtime_lifecycle
- asset_evidence

## 排除的 Sensitivity
- L3+
- L4

## 默认 Token Budget
3000

## Required Core Memory
- **MEM-20260603-SA-002** — AI Company OS 七层架构与 P0/P1/P2 成熟度路线（必须引用）

## 使用说明
1. 扫描 approved/ 下所有 system_architecture、governance_rule、runtime_lifecycle、asset_evidence 类型的 memory
2. 按 sensitivity <= L2 过滤
3. 按 view_a_stage 和 view_b_layer 匹配当前任务
4. 按 priority (core > normal > reference) 排序
5. 在 token budget 内取 top N
6. 取每条 memory 的 summary 和 selected_context（非全文）
7. 生成 Context Pack 写入 private/memory/context-packs/generated/

## 架构审查检查项（对应 SA-002 三问框架）
在每次架构审查中必须回答：

1. **A 视角定位：** 本任务属于经营闭环哪一段？
2. **B 视角定位：** 本任务属于 OS 技术支撑哪一层？
3. **P0/P1/P2 判断：** 当前做的是哪一级？是否提前做了 P2？
4. **三服务验证：**
   - 是否增强真实产品线运行？
   - 是否形成可复用 OS 能力？
   - 是否新增公司资产沉淀？
5. **Memory 关联：** 本次审查结论是否需要生成新的 memory candidate？
