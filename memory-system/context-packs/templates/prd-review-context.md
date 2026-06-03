# Context Pack Template — PRD Review
# v0.46 P0 — 选择规则模板

## 任务类型
prd_review

## View A 经营阶段
- productization

## View B 技术层
- governance_kernel
- company_memory_context_layer

## 包含的 Memory 类型
- founder_decision
- governance_rule
- system_architecture
- runtime_lifecycle

## 排除的 Sensitivity
- L3+
- L4

## 默认 Token Budget
4000

## 使用说明
1. 扫描 approved/ 下 founder_decision、governance_rule、system_architecture、runtime_lifecycle
2. sensitivity <= L2
3. 匹配 view_a_stage 包含 productization
4. 取 summary + 关键决策内容（非全文）
5. 重点关注 founder_decision 类型
6. 生成 Context Pack
