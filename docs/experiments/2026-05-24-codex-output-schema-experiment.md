# Task 4: `--output-schema` 实验记录

> 日期：2026-05-24
> 环境：Codex v0.130.0, gpt-5.4, `CODE_RUNTIME=real`
> 仓库：ai-company-os

## 实验 1：基础 JSON 结构

**Schema**: `patch_spec_schema.json`（不含 diff 字段）
**Prompt**: "Analyze this repo and tell me what the factory.py file does and how it decides between mock and real mode"

**结果**: ✅ 纯 JSON 输出，无 markdown 包裹

```json
{
  "plan_summary": "...",
  "risk": "low",
  "impact": "...",
  "files": [
    { "path": "backend/app/runtime/code_capable/factory.py", "change": "..." },
    ...
  ]
}
```

```
Elapsed: ~20s
```

## 实验 2：含 git diff 的 JSON 结构

**Schema**: 同上 + `diff` 字段
**Prompt**: "If you were to add a new 'claude_code' mode check, describe the change plan and output the git diff"

**结果**: ✅ 完整 git diff 嵌入 JSON diff 字段

```
Diff length: 3,253 chars
Files in diff: 2
@@ hunks: 3
git apply --check: PASS (exit 0)
git apply: SUCCESS → git checkout: CLEAN
Elapsed: ~25s
```

## 关键约束

1. **OpenAI `required` 强制所有属性必需** — `required` 数组必须包含 `properties` 中的所有 key
2. **Schema 校验严格** — 错误的 `required` 直接返回 `400 invalid_json_schema`
3. **`additionalProperties: false` 生效** — 多余字段不会被模型添加
4. **嵌套对象校验** — `files[].path` + `files[].change` 被正确执行

## 结论

`--output-schema` 是稳定可用的。Codex Patch 路径可以从「不稳定文本解析」升级为「结构化 JSON + 有效 git diff」，在复杂重构时作为备选路径。
