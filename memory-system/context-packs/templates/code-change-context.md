# Context Pack Template — Code Change
# v0.46 P0 — 选择规则模板

## 任务类型
code_change

## View A 经营阶段
- build_production

## View B 技术层
- runtime_adapter_layer
- asset_evidence_registry

## 包含的 Memory 类型
- runtime_lifecycle
- governance_rule
- workflow_pattern

## 排除的 Sensitivity
- L2+
- L3
- L4

## 默认 Token Budget
2000

## 使用说明
1. 扫描 approved/ 下 runtime_lifecycle、governance_rule、workflow_pattern 类型
2. 仅 sensitivity <= L1
3. 按 priority 排序
4. 取 summary（不取全文 — Codex 不需要完整架构上下文）
5. 生成 Context Pack
