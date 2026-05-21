# Registry Phase 1 完成报告

**日期**: 2026-03-27
**项目**: novel-v1
**状态**: ✅ 完成

---

## 📁 Registry 文件结构

```
novel-v1/
├── registry/
│   ├── project-registry.yaml    # 项目层入口
│   ├── asset-registry.yaml      # 资产清单
│   ├── execution-registry.yaml  # 执行记录
│   └── knowledge-registry.yaml # 知识卡片
├── manuscripts/                 # 实际文件
└── asset-layer-phase1.md       # 原始数据
```

---

## 📊 初始数据统计

| Registry | 记录数 | 说明 |
|----------|--------|------|
| Project | 1 | novel-v1 |
| Asset | 10 | 7 published + 3 archived |
| Execution | 5 | Test-01~03, Test-02-v2, Test-03-v2 |
| Knowledge | 9 | 规则(3) + 成功(3) + 失败(3) |

---

## 📋 字段规范

### ID 规范

| 类型 | 格式 | 示例 |
|------|------|------|
| project_id | {name}-v{version} | novel-v1 |
| asset_id | asset-{project}-{type}-{seq} | asset-novel-test-01-final |
| record_id | record-{task_id} | record-test-01-01 |
| card_id | card-{type}-{seq} | card-workflow-001 |

### 状态字段

| 字段 | 值 |
|------|------|
| status | draft / reviewed / approved / archived / published |
| review_status | pending / passed / failed |
| copyright_status | unchecked / low / medium / high |
| publish_status | unpublished / ready / published |

---

## 🔄 新资产进入 Registry 流程

### 步骤 1: 任务完成 → 文件落盘

```
writer 完成 → 保存到 manuscripts/YYYY-MM-DD/{task_id}.md
review 通过 → 导出为 docx
```

### 步骤 2: 生成 asset_id

```
格式: asset-{project}-{asset_type}-{seq}
示例: asset-novel-novel-018
```

### 步骤 3: 写入 Asset Registry

```yaml
- asset_id: asset-novel-novel-018
  project_id: novel-v1
  asset_type: novel
  title: ...
  status: published
  source_task: novel-18
  review_status: passed
  copyright_status: low
  publish_status: published
  file_path: manuscripts/2026-03-28/novel-18-标题.docx
  created_at: 2026-03-28
  updated_at: 2026-03-28
```

### 步骤 4: 更新 Execution Record

```yaml
- record_id: record-novel-18
  task_id: novel-18
  project_id: novel-v1
  agent_chain: [...]
  timeout_count: 0
  fallback_history: []
  degradation_flag: false
  result: passed
  export_status: success
  completed_at: 2026-03-28Txx:xx:xxZ
```

### 步骤 5: 如有知识沉淀 → 更新 Knowledge Registry

```yaml
- card_id: card-workflow-005
  card_type: workflow_lesson
  title: ...
  source_project: novel-v1
  key_rules: [...]
  created_at: 2026-03-28
```

---

## ✅ Registry Phase 1 完成确认

- [x] Project Registry 初始数据
- [x] Asset Registry 初始数据
- [x] Execution Records 初始数据
- [x] Knowledge Registry 初始数据
- [x] 统一 ID 规范
- [x] 状态字段定义
- [x] 新资产进入流程

---

## 下一步（Phase 2）

1. 接入 novel-15, novel-16 到 Asset Registry
2. 实现查询能力（按 project/status/type 查询）
3. 自动 digest 生成

---

## 📂 产出文件

| 文件 | 路径 |
|------|------|
| Project Registry | `novel-v1/registry/project-registry.yaml` |
| Asset Registry | `novel-v1/registry/asset-registry.yaml` |
| Execution Records | `novel-v1/registry/execution-registry.yaml` |
| Knowledge Registry | `novel-v1/registry/knowledge-registry.yaml` |