# novel-v1 Asset & Knowledge Layer - Phase 1 Output

## 1️⃣ Asset List（资产清单）

### Test-01: 合同婚姻到期后的最后一天

| asset_id | project_id | asset_type | title | status | review_status | copyright_status | file_path | source_task |
|----------|-------------|------------|-------|--------|---------------|-------------------|-----------|-------------|
| asset-novel-test-01-final | novel-v1 | novel | 合同婚姻到期后的最后一天 | published | passed | low | Test-01-合同婚姻.docx | Test-01-01 |
| asset-novel-test-01-md | novel-v1 | markdown | 合同婚姻到期后的最后一天 | archived | passed | low | Test-01-合同婚姻.md | Test-01-01 |

### Test-02: 被裁员前的最后一次汇报

| asset_id | project_id | asset_type | title | status | review_status | copyright_status | file_path | source_task |
|----------|-------------|------------|-------|--------|---------------|-------------------|-----------|-------------|
| asset-novel-test-02-final | novel-v1 | novel | 被裁员前的最后一次汇报 | published | passed | low | Test-02-被裁员汇报.md | Test-02-01 |
| asset-novel-test-02-docx | novel-v1 | docx | 被裁员前的最后一次汇报 | ready | passed | low | - | Test-02-01 |

### Test-03: 她收到了一封来自三年前的邮件

| asset_id | project_id | asset_type | title | status | review_status | copyright_status | file_path | source_task |
|----------|-------------|------------|-------|--------|---------------|-------------------|-----------|-------------|
| asset-novel-test-03-final | novel-v1 | novel | 她收到了一封来自三年前的邮件 | published | passed | low | Test-03-三年前邮件.md | Test-03-01 |
| asset-novel-test-03-docx | novel-v1 | docx | 她收到了一封来自三年前的邮件 | ready | passed | low | - | Test-03-01 |

### Test-02-v2: 三十年后与初恋重逢

| asset_id | project_id | asset_type | title | status | review_status | copyright_status | file_path | source_task |
|----------|-------------|------------|-------|--------|---------------|-------------------|-----------|-------------|
| asset-novel-test-02v2-final | novel-v1 | novel | 三十年后与初恋重逢 | published | passed | low | Test-02-v2-初恋重逢.docx | Test-02-v2-01 |
| asset-novel-test-02v2-md | novel-v1 | markdown | 三十年后与初恋重逢 | archived | passed | low | Test-02-v2-初恋重逢.md | Test-02-v2-01 |

### Test-03-v2: 少年重生北伐革命时期

| asset_id | project_id | asset_type | title | status | review_status | copyright_status | file_path | source_task |
|----------|-------------|------------|-------|--------|---------------|-------------------|-----------|-------------|
| asset-novel-test-03v2-final | novel-v1 | novel | 少年重生北伐革命时期 | published | passed | low | Test-03-v2-北伐革命.docx | Test-03-v2-01 |
| asset-novel-test-03v2-md | novel-v1 | markdown | 少年重生北伐革命时期 | archived | passed | low | Test-03-v2-北伐革命.md | Test-03-v2-01 |

---

### 统计

| 指标 | 数量 |
|------|------|
| 总资产数 | 11 |
| 已发布 (published) | 5 |
| 已就绪 (ready) | 2 |
| 已归档 (archived) | 4 |
| 版权通过 (low) | 11 |
| 审核通过 | 11 |

---

## 2️⃣ Execution Records（执行记录清单）

### Test-01 合同婚姻

| task_id | agent_chain | timeout_count | fallback_history | degradation_flag | result | export_status |
|---------|-------------|---------------|------------------|------------------|--------|---------------|
| Test-01-01 | lead-novel → story-editor → writer → review-editor | 2 | [standard→lite (story), standard→lite (writer)] | false | passed | success |

### Test-02 被裁员汇报

| task_id | agent_chain | timeout_count | fallback_history | degradation_flag | result | export_status |
|---------|-------------|---------------|------------------|------------------|--------|---------------|
| Test-02-01 | lead-novel → story-editor → writer → review-editor | 2 | [standard→lite (writer x2)] | false | passed | success |

### Test-03 三年前邮件

| task_id | agent_chain | timeout_count | fallback_history | degradation_flag | result | export_status |
|---------|-------------|---------------|------------------|------------------|--------|---------------|
| Test-03-01 | lead-novel → story-editor → writer → review-editor | 3 | [standard→lite→segmented (writer)] | false | passed | success |

### Test-02-v2 初恋重逢

| task_id | agent_chain | timeout_count | fallback_history | degradation_flag | result | export_status |
|---------|-------------|---------------|------------------|------------------|--------|---------------|
| Test-02-v2-01 | lead-novel → story-editor → writer → review-editor | 1 | [standard→lite (story)] | false | passed | success |

### Test-03-v2 北伐革命

| task_id | agent_chain | timeout_count | fallback_history | degradation_flag | result | export_status |
|---------|-------------|---------------|------------------|------------------|--------|---------------|
| Test-03-v2-01 | lead-novel → story-editor → writer → review-editor | 0 | [] | false | passed | success |

---

### 统计

| 指标 | 数量 |
|------|------|
| 总任务数 | 5 |
| 超时任务数 | 3 |
| 总超时次数 | 8 |
| 有 fallback | 4 |
| 有 degradation | 0 |
| 全部通过 | 5 |

---

## 3️⃣ Knowledge Candidates（知识候选）

### 可复用规则

| card_id | card_type | title | key_rules | source_project |
|---------|-----------|-------|-----------|----------------|
| card-workflow-001 | workflow_lesson | 串行测试稳定性验证 | 1. medium任务默认lite模式 2. 串行执行降低超时率 3. fallback自动切换 | novel-v1 |
| card-workflow-002 | workflow_lesson | lite模式有效性 | 1. lite模式产出质量达标 2. 字数降至4000-6000可接受 3. 适用于中等复杂度任务 | novel-v1 |
| card-asset-001 | asset_lesson | 资产沉淀最小集 | 1. 每任务产出至少2个资产(final+md) 2. docx为发布资产 3. md为归档资产 | novel-v1 |

### 成功经验

| card_id | card_type | title | summary | source_project |
|---------|-----------|-------|---------|----------------|
| card-success-001 | success_case | 串行模式零超时 | Test-03-v2使用串行+lite，0超时，闭环完成 | novel-v1 |
| card-success-002 | success_case | 多任务不崩溃 | 并行测试验证系统可同时处理多任务不崩 | novel-v1 |
| card-success-003 | success_case | fallback自动恢复 | timeout后自动切换lite模式继续执行 | novel-v1 |

### 失败/问题点

| card_id | card_type | title | problem | lesson | source_project |
|---------|-----------|-------|---------|--------|----------------|
| card-fail-001 | failure_case | writer超时主因 | 12000字全量写作超时 | 1. 默认使用lite 2. 超时分段 | novel-v1 |
| card-fail-002 | failure_case | scene数量失控 | 7+ scenes导致review输入过大 | 短篇场景控制5-7 | novel-v1 |
| card-fail-003 | failure_case | export后未收口 | 部分任务export后未更新TASK-POOL | export后必须更新 | novel-v1 |

---

## 📋 汇总

| 类别 | 数量 |
|------|------|
| 资产清单 | 11 项 |
| 执行记录 | 5 条 |
| 知识卡片候选 | 9 条 |

---

## 下一步

这批数据将作为：
1. Asset Registry 初始数据 ✅
2. Knowledge Layer 初始卡片 ✅
3. 可直接接入 Registry 系统