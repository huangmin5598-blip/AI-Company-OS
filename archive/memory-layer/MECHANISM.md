# AI Company OS - Memory Layer 机制说明

## 一、统一触发点

**触发事件**：`task_completed_event`

当任意项目任务完成时，触发以下统一链路：

```
task_completed_event
    ↓
asset_processor
    ↓
registry_writer
    ↓
写入 Registry
```

**触发条件**：
- task_status = done / completed
- review_status = PASS

---

## 二、Asset Processor 职责

**核心功能**：接收 task_completed_event，将项目产出转换为标准资产结构

**输入**：
- project_id
- task_id
- asset_type
- output_path
- title
- summary
- metadata

**输出**：
- asset_record（写入 Asset Registry）
- execution_record（写入 Execution Records）
- project_update（更新 Project Registry）
- knowledge_candidate（可选）

**不负责**：
- 查询 Registry
- 业务逻辑判断
- 内容质量分析

---

## 三、Registry Writer 职责

**核心功能**：纯写入层，负责将标准化数据写入各 Registry

**写入范围**：
1. Asset Registry（资产记录）
2. Execution Records（执行记录）
3. Project Registry（项目状态）
4. Knowledge Registry（知识候选，可选）

**不负责**：
- 解析项目类型
- 判断内容质量
- 生成摘要
- 业务逻辑分支

---

## 四、新项目接入方式

只需调用统一命令，无需为新项目写专用脚本：

```bash
# Step 1: 生成标准资产包
python asset_processor.py \
  --project {project_id} \
  --task {task_id} \
  --type {asset_type} \
  --title "{标题}" \
  --summary "{摘要}" \
  --path {output_path} \
  --metadata '{JSON对象}'

# Step 2: 写入 Registry
python registry_writer.py --input {bundle_file}
```

**新项目接入只需传入**：
- project_id
- task_id
- asset_type
- output_path
- metadata（可扩展）

---

## 五、已验证资产类型

### 内容类
| 类型 | 说明 | metadata 扩展 |
|------|------|---------------|
| novel | 短篇小说 | genre, word_count, chapters |
| article | 文章 | platform, topic, seo_keywords |
| image | 图片 | prompt_ref, size, style |
| video_script | 视频脚本 | duration, platform, shot_count |
| social_post | 社交帖子 | platform, character_count |

### 文档类
| 类型 | 说明 | metadata 扩展 |
|------|------|---------------|
| document | 文档资产 | file_format, use_case, page_count |
| report | 报告 | report_type, period, stakeholders |
| prd | 产品需求 | product_name, stage, target_users |

### 系统类
| 类型 | 说明 | metadata 扩展 |
|------|------|---------------|
| protocol | 协议/规范 | protocol_name, version, scope |
| workflow | 工作流 | workflow_name, trigger, steps |
| prompt_template | 提示词模板 | template_name, model, variables |
| code | 代码模块 | language, module, framework |

---

## 六、核心原则

1. **不以具体项目为中心**：统一触发点是 task_completed_event，不是 export-docx
2. **不以 export 为唯一入口**：某些资产类型（protocol, workflow）可能没有 docx
3. **状态层与内容层分离**：Asset Processor 负责标准化，Registry Writer 负责写入
4. **通用写入器**：Registry Writer 不区分项目类型，不允许专用脚本
5. **差异仅在 metadata**：新项目类型通过 asset_type + metadata 扩展，不复制流程

---

## 七、文件结构

```
/memory-layer
  /schemas
    task_completed_event.schema.json
    asset_record.schema.json
    execution_record.schema.json
  /processors
    asset_processor.py      ← 通用，参数化
  /writers
    registry_writer.py     ← 通用，统一写入
  /registry
    asset-registry.json
    execution-records.json
    project-registry.json
    knowledge-registry.json
```

---

## 八、调用示例

### 示例1：小说资产
```bash
python asset_processor.py \
  --project novel-v1 \
  --task novel-17 \
  --type novel \
  --title "契约婚姻：闪婚甜宠" \
  --summary "财阀继承人与普通女孩契约结婚" \
  --path "/path/to/novel-17.docx" \
  --metadata '{"genre": "闪婚甜宠", "word_count": 11000}'
```

### 示例2：文章资产
```bash
python asset_processor.py \
  --project content-lab-v1 \
  --task article-001 \
  --type article \
  --title "AI开发者生存指南" \
  --summary "探讨独立开发者的机遇与挑战" \
  --path "/path/to/article.md" \
  --metadata '{"platform": "medium", "topic": "AI"}'
```

### 示例3：代码资产
```bash
python asset_processor.py \
  --project infra-v1 \
  --task code-001 \
  --type code \
  --title "Asset Processor" \
  --summary "通用资产处理模块" \
  --path "/path/to/asset_processor.py" \
  --metadata '{"language": "python", "module": "asset_processor"}'
```
