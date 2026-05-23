# v0.4 Company Memory MVP — 执行计划

> **基于 PRD** `AI-COMPANY-CONTROL-CENTER-v0.4-COMPANY-MEMORY-MVP-PRD.md`
> **预估工时**: 10-14h（约 1.5-2 天冲刺）
> **执行顺序**: Day 1（后端 + 数据迁移）→ Day 2（CEO Skill 增强 + 前端 + 验收）

---

## 执行概览

```
Day 1 (5-7h)
├── org_memory 表 + FTS5 虚拟表
├── knowledge_proposals 表
├── context_packs 追加 referenced_memory_ids 字段
├── 6 个新 API 端点
├── 幂等 from-learning-candidate 逻辑
└── 数据迁移：已有 approved Learning Candidate → proposals

Day 2 (5-7h)
├── CEO Skill 增强（memory recall 集成）
├── /memory 前端页面（搜索/过滤/来源链）
├── Knowledge Proposal 确认面板
├── 验收：双闭环
└── Roadmap 更新
```

---

## Day 1：后端 + 数据层

### Step 1: 创建 org_memory 模型

文件: `backend/app/models/org_memory.py`

```python
from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base

class OrgMemory(Base):
    __tablename__ = "org_memory"

    id = Column(Integer, primary_key=True)
    memory_type = Column(String, nullable=False)
    # failure_pattern / decision_pattern / tool_gap / context_update / sop_hint
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    business_line = Column(String, nullable=True)
    tags = Column(Text, nullable=True)                              # JSON array
    source_type = Column(String, nullable=True)
    source_id = Column(String, nullable=True)
    source_candidate_id = Column(Integer, nullable=True)
    source_task_id = Column(Integer, nullable=True)
    source_review_id = Column(Integer, nullable=True)
    source_goal_session_id = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    status = Column(String, default="active")                        # active / superseded / expired / archived
    version = Column(Integer, default=1)
    supersedes_memory_id = Column(Integer, nullable=True)
    export_status = Column(String, default="not_exported")           # not_exported / exported / pending / failed
    knowledge_os_path = Column(String, nullable=True)
    knowledge_os_slug = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

### Step 2: 创建 FTS5 虚拟表支持（含 capability check + LIKE fallback）

FTS5 在 SQLAlchemy 中需要额外处理。方案：

**Capability check**：启动时检测 SQLite 是否编译了 FTS5：

```python
import sqlite3

def fts5_available() -> bool:
    try:
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS test_fts USING fts5(content)")
        conn.close()
        return True
    except Exception:
        return False
```

**主路径（FTS5 可用时）**：

不通过 SQLAlchemy ORM 管理 FTS5 表，直接通过 raw SQL 创建：

```python
# 在 init_db() 或 migrate 脚本中执行，先检测 capability
if fts5_available():
    CREATE VIRTUAL TABLE IF NOT EXISTS org_memory_fts USING fts5(
      title, summary, content, tags,
      content='org_memory',
      content_rowid='id'
    );
```

并创建触发器保持同步：

```sql
CREATE TRIGGER IF NOT EXISTS org_memory_ai AFTER INSERT ON org_memory BEGIN
  INSERT INTO org_memory_fts(rowid, title, summary, content, tags)
  VALUES (new.id, new.title, new.summary, new.content, new.tags);
END;
CREATE TRIGGER IF NOT EXISTS org_memory_ad AFTER DELETE ON org_memory BEGIN
  INSERT INTO org_memory_fts(org_memory_fts, rowid, title, summary, content, tags)
  VALUES ('delete', old.id, old.title, old.summary, old.content, old.tags);
END;
CREATE TRIGGER IF NOT EXISTS org_memory_au AFTER UPDATE ON org_memory BEGIN
  INSERT INTO org_memory_fts(org_memory_fts, rowid, title, summary, content, tags)
  VALUES ('delete', old.id, old.title, old.summary, old.content, old.tags);
  INSERT INTO org_memory_fts(rowid, title, summary, content, tags)
  VALUES (new.id, new.title, new.summary, new.content, new.tags);
END;
```

**Fallback 路径（FTS5 不可用时）**：

使用 `LIKE` 查询替代，在 `/api/v1/memory/search` 端点中动态切换：

```python
def search_memory(query: str, business_line: str = None, memory_type: str = None):
    if fts5_available():
        # FTS5 MATCH 查询（需 sanitize）
        ...
    else:
        # LIKE fallback — 系统不崩溃
        stmt = select(OrgMemory).where(
            OrgMemory.status == "active",
            or_(
                OrgMemory.title.ilike(f"%{query}%"),
                OrgMemory.summary.ilike(f"%{query}%"),
                OrgMemory.content.ilike(f"%{query}%"),
                OrgMemory.tags.ilike(f"%{query}%"),
            )
        )
```

**系统不崩保障**：
- 所有 `/api/v1/memory/search` 和 `/api/v1/memory/recall` 端点内置 `fts5_available()` 检测
- FTS5 不可用时静默降级为 LIKE 搜索
- 不因 FTS5 错误导致 500 响应

文件: `backend/app/models/fts_triggers.py` 包含 capability check 和 fallback 逻辑。

### Step 3: 创建 knowledge_proposals 模型

文件: `backend/app/models/knowledge_proposal.py`

```python
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base

class KnowledgeProposal(Base):
    __tablename__ = "knowledge_proposals"

    id = Column(Integer, primary_key=True)
    source_candidate_id = Column(Integer, nullable=False, unique=True)  # FK → learning_candidates.id, 唯一约束保证幂等
    proposal_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    structured_content = Column(Text, nullable=True)       # JSON
    target_memory_type = Column(String, nullable=False)
    business_line = Column(String, nullable=True)
    status = Column(String, default="draft")               # draft / committed / revised / rejected / expired
    org_memory_id = Column(Integer, nullable=True)         # committed 时设置 → FK org_memory.id
    committed_at = Column(DateTime, nullable=True)         # committed 时设置
    founder_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
```

### Step 4: context_packs 追加字段

使用 `ALTER TABLE` 或直接更新 model 文件（建议直接更新 model + 手动 alter 已有表）：

在 `backend/app/models/context_pack.py` 追加：

```python
referenced_memory_ids = Column(Text, nullable=True)  # JSON: [memory.id, ...]
```

### Step 5: 注册到 models/__init__.py

### Step 6: 创建 Pydantic Schemas（含枚举校验）

文件:
- `backend/app/schemas/org_memory.py` — OrgMemoryCreate, OrgMemoryResponse, MemorySearchResult
- `backend/app/schemas/knowledge_proposal.py` — KnowledgeProposalCreate, KnowledgeProposalResponse, KnowledgeProposalDecisionRequest
- `backend/app/schemas/memory_recall.py` — MemoryRecallRequest, MemoryRecallResponse

枚举校验：
```python
from enum import Enum

class MemoryType(str, Enum):
    failure_pattern = "failure_pattern"
    decision_pattern = "decision_pattern"
    tool_gap = "tool_gap"
    context_update = "context_update"
    sop_hint = "sop_hint"

class MemoryStatus(str, Enum):
    active = "active"
    superseded = "superseded"
    expired = "expired"
    archived = "archived"

class ProposalType(str, Enum):
    failure_pattern = "failure_pattern"
    decision_pattern = "decision_pattern"
    tool_gap = "tool_gap"
    context_update = "context_update"
    sop_hint = "sop_hint"

class ProposalStatus(str, Enum):
    draft = "draft"
    committed = "committed"
    revised = "revised"
    rejected = "rejected"
    expired = "expired"
```

所有 Pydantic schema 中使用这些 Enum 做字段类型校验，确保无效值在 HTTP 请求层即被拒绝。

### Step 7: 创建 Router — memory entries

文件: `backend/app/routers/memory_entries.py`

端点:
- `GET /api/v1/memory/entries` — 列表（筛选: business_line, memory_type, status）
- `GET /api/v1/memory/entries/{id}` — 详情（含来源链：candidate → review → task → goal_session）
- `POST /api/v1/memory/entries` — 手动创建（admin）

### Step 8: 创建 Router — memory search (FTS5 + sanitize + LIKE fallback)

文件: `backend/app/routers/memory_search.py`

端点:
- `GET /api/v1/memory/search` — 全文搜索
  - 参数: q（搜索关键词）, business_line, memory_type
  - 返回 top 20 结果，每个结果含 snippet
  - 内置 FTS5 capability check，不可用时降级 LIKE

**FTS5 query sanitize**：防止特殊字符导致 MATCH 报错

```python
import re

def sanitize_fts5_query(raw: str) -> str:
    """Sanitize FTS5 query: escape special chars, fallback to LIKE-safe string."""
    if not raw or not raw.strip():
        return ""
    # FTS5 special characters: ^ * ( ) { } [ ] " ~ + -
    # Replace with space, keep alphanumeric + CJK chars
    sanitized = re.sub(r'[^\w\u4e00-\u9fff\s]', ' ', raw)
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    if not sanitized:
        return ""
    terms = sanitized.split()
    return ' OR '.join(terms)
```

**搜索函数（动态切换 FTS5 / LIKE）**：

```python
def search_memory(query: str, business_line: str = None, memory_type: str = None):
    if not query or not query.strip():
        return []

    if fts5_available():
        fts_query = sanitize_fts5_query(query)
        if not fts_query:
            return []
        # FTS5 MATCH with sanitized query
        sql = """
            SELECT o.*, snippet(org_memory_fts, 0, '<b>', '</b>', '...', 32) as snippet
            FROM org_memory_fts
            JOIN org_memory o ON o.id = org_memory_fts.rowid
            WHERE org_memory_fts MATCH ? AND o.status = 'active'
            ORDER BY rank
            LIMIT 20
        """
    else:
        # LIKE fallback — 系统不崩溃
        stmt = select(OrgMemory).where(
            OrgMemory.status == "active",
            or_(
                OrgMemory.title.ilike(f"%{query}%"),
                OrgMemory.summary.ilike(f"%{query}%"),
                OrgMemory.content.ilike(f"%{query}%"),
                OrgMemory.tags.ilike(f"%{query}%"),
            )
        ).limit(20)
```

**Fallback 行为**：
- FTS5 不可用时，搜索结果不如 FTS5 精确（无 rank/snippet），但系统不崩溃
- 每次请求都检查 capability，支持运行时切换
- LIKE fallback 不含 snippet 标注，搜索结果以纯文本返回

### Step 9: 创建 Router — memory recall (CEO Agent 专用，中文友好)

文件: `backend/app/routers/memory_recall.py`

端点:
- `POST /api/v1/memory/recall`

输入:
```json
{ "goal_summary": "亚马逊选品连续失败排查", "business_line": "amazon-seller" }
```

**中文友好策略**（不依赖简单空格分词，使用 goal_summary + business_line + 多字段 fallback）：

```python
def build_recall_query(goal_summary: str, business_line: str = None) -> list:
    """
    中文场景下不使用空格分词。
    
    策略:
    1. 先用 goal_summary 整体 + business_line 在 title/summary/tags 中搜索
    2. 若结果 < 3 条，从 goal_summary 按中文标点切割提取关键词片段
       （按 / ， 。、！？分割取前 3 段），用这些片段在 title/summary 二次搜索
    3. 若结果仍 < 3 条，用 business_line 单独搜索
    4. 去重排序，取 top 3
    """
    pass
```

逻辑:
1. **主搜索**：用 `goal_summary` 整体 + `business_line` 在 `org_memory_fts` 或 LIKE 中搜索
2. **辅助搜索**：若结果 < 3 条，从 `goal_summary` 提取 2-3 个关键词片段（按 `/ ，。、！？` 分割取前 3 段），用这些片段在 title/summary 中二次搜索
3. 按 `status=active` 过滤
4. 去重排序，取 top 3
5. **空结果不阻断**：返回空数组 `[]` 时，CEO Agent 正常进行 Goal Intake

返回格式:
```json
{
  "memories": [
    { "memory_id": 1, "title": "...", "summary": "...", "memory_type": "failure_pattern", "confidence": 0.85 }
  ],
  "recall_query": "关键词",
  "total": 1
}
```

### Step 10: 创建 Router — knowledge proposals

文件: `backend/app/routers/memory_proposals.py`

端点:
- `GET /api/v1/memory/knowledge-proposals` — 列表（筛选: status, proposal_type, business_line）
- `POST /api/v1/memory/knowledge-proposals` — 手动创建
- `PATCH /api/v1/memory/knowledge-proposals/{id}/decide` — Founder 确认决策

Decide 逻辑:
- approved → 将 proposal 写入 org_memory（status=active）→ 更新 proposal: status=committed, org_memory_id=新建记忆的 id, committed_at=now()
  - 先检查 proposal.org_memory_id 是否已存在：若已存在 → 返回 409 Conflict + 提示"该 proposal 已 commit，不可重复操作"
- revised → 更新 proposal 字段（founder_notes 等），status 保持 draft
- rejected → proposal status=expired

### Step 11: 创建 Router — from-learning-candidate (幂等生成)

文件: `backend/app/routers/memory_from_candidate.py`

端点:
- `POST /api/v1/memory/from-learning-candidate/{id}`

逻辑:
1. 校验 candidate 存在且 approval_status=approved
2. 幂等检查：检查是否已有 KnowledgeProposal 的 source_candidate_id={id}
   - 若有 → 返回已有 proposal（200，不创建新数据）
   - 若无 → 继续
3. 根据 candidate 信息自动生成 Knowledge Proposal 草稿:
   - proposal_type = candidate.candidate_type
   - target_memory_type = 映射（failure_pattern / decision_pattern / tool_gap / context_update / sop_hint）
   - title = 从 candidate.summary 提取
   - summary = candidate.summary
   - structured_content = 从 candidate.recommendation 构建
   - business_line = 从关联 task 推断
   - status = draft
4. 写入 knowledge_proposals
5. 返回新创建的 proposal

### Step 12: 注册到 routers/__init__.py

### Step 13: 数据迁移脚本

文件: `backend/scripts/migrate_v0_4_learning_candidates.py`

脚本逻辑:
1. 查询所有 approval_status=approved 的 learning_candidates
2. 对于每个 candidate，调用 from-learning-candidate 逻辑生成 proposal
3. 打印迁移结果

不需要自动执行，Founder 可以选择运行。

### Step 14: 验证

```
cd backend && python -c "from app.database import init_db; init_db(); print('DB init OK')"
cd backend && python -c "
from app.main import app
routes = [r.path for r in app.routes if '/api/v1/memory' in r.path]
print(f'Memory routes: {len(routes)}')
for r in sorted(routes): print(f'  {r}')
"
cd backend && python -c "
from app.database import get_sync_session
# Verify FTS5 table
session = get_sync_session()
result = session.execute('SELECT name FROM sqlite_master WHERE type=\\'table\\' AND name=\\'org_memory_fts\\'')
print(f'FTS5 table exists: {result.first() is not None}')
session.close()
"
```

---

## Day 2：CEO Skill 增强 + 前端 + 验收

### Step 15: 增强 Hermes CEO Skill

修改 `~/.hermes/skills/ceo-agent/skill.md`：

在 Goal Intake workflow 的 Step 1 之后新增：

```
1a. 调用 /api/v1/memory/recall
    POST http://127.0.0.1:8001/api/v1/memory/recall
    Body: { "goal_summary": "用户的目标摘要", "business_line": "推断的业务线" }
    返回 top 3 相关记忆
    
    如果召回结果非空，拆解时加入 memory_references：
    "memory_references": [
      { "memory_id": 12, "title": "...", "reason": "..." }
    ]
    
    创建的 Context Pack 写入 referenced_memory_ids
```

同时在 safety rules 中增加：

```
9. Memory recall 是辅助参考，不强约束拆解逻辑。
10. 若召回为空，不影响拆解正常进行。
```

### Step 16: 创建 /memory 前端页面

文件: `frontend/src/app/memory/page.tsx`

页眉: "🧠 Company Memory 组织记忆"

布局:
- 顶部：FTS5 搜索框 + business_line 下拉 + memory_type 下拉
- 搜索结果区域：
  - 卡片列表，每张卡片显示：
    - 标题 + 记忆类型标签（带颜色：failure_pattern=🔴, decision_pattern=🟡, tool_gap=🔧, context_update=💡, sop_hint=📋）
    - 摘要 snippet（高亮搜索关键词）
    - business_line 标签
    - 状态 badge（active=绿色, superseded=灰色, expired=灰色）
    - 版本号（如果 version > 1）
    - 来源链（MVP 优先显示文字链，点击跳转后置）：
      ```
      📄 learning_candidate #3 → 📝 review #2 → 📋 task #1 → 🎯 goal_session #1
      ```
      MVP 先只显示来源链文字，不要求点击跳转；点击跳转归入后续迭代。
  - 分页或滚动加载

右侧面板 / 底部 Tab:
- "待处理 Knowledge Proposals" 区域
  - 显示所有 status=draft 的 proposals
  - 每条显示：标题、类型、来源 candidate
  - 操作按钮：✅ 确认 / ✏️ 修改 / ❌ 拒绝
  - 确认时弹出确认框（含 notes 输入）

空状态: "暂无组织记忆。Learning Candidate 批准后会自动生成 Knowledge Proposal。"

### Step 17: 更新 Navbar

在 layout.tsx 的 NavBar 中，在 "CEO" 链接后添加：

```
<NavLink href="/memory" label="记忆" />
```

### Step 18: 更新 Roadmap

- v0.3 标记完成
- v0.4 标记 PRD 已编写
- 后续版本顺序修正

### Step 19: 验收

#### 验收 1: Learning Candidate → Org Memory

```
1. POST /api/v1/memory/from-learning-candidate/{approved_candidate_id}
   → 返回 Knowledge Proposal (draft)
2. 重复调用 → 幂等，返回相同 proposal
3. PATCH /api/v1/memory/knowledge-proposals/{id}/decide
   Body: {"status": "approved"}
   → org_memory 新增 1 条 (status=active)
4. GET /api/v1/memory/search?q=关键词
   → 返回该记忆
```

#### 验收 2: CEO Agent 召回

```bash
1. POST /api/v1/memory/recall
   Body: {"goal_summary": "amazon seller API 400 错误修复", "business_line": "amazon"}
   → 返回 top 3 相关记忆（含之前写入的 amazon-seller failure pattern）
2. POST /api/v1/memory/recall
   Body: {"goal_summary": "完全不相关的古文研究", "business_line": "literature"}
   → 返回空数组 []
   → CEO Agent 正常进行 Goal Intake，不走异常路径
```

#### 验收 3: Memory 页面（MVP）

```bash
1. 浏览器打开 /memory
2. 搜索关键词 → 结果含高亮 snippet（FTS5）或正常显示（LIKE fallback）
3. 按 business_line 过滤 → 结果更新
4. 按 memory_type 过滤 → 结果更新
5. 展开详情 → 显示完整来源链（文字链，不要求点击跳转）
6. 查看 Knowledge Proposals → 显示待处理条数
```

#### 验收 4: 幂等检查

```bash
1. POST /api/v1/memory/from-learning-candidate/{id}（第一次）
   → 返回 201 + 新 proposal
2. POST /api/v1/memory/from-learning-candidate/{id}（第二次）
   → 返回 200 + 相同 proposal（不重复创建）
3. PATCH /api/v1/memory/knowledge-proposals/{id}/decide
   Body: {"status": "approved"}
   → 返回 200 + proposal.status=committed + org_memory_id 非空
4. PATCH /api/v1/memory/knowledge-proposals/{id}/decide（重复操作）
   → 返回 409 + 提示已 commit，org_memory 不重复写入
```

#### 验收 5: FTS5 不可用不崩溃

```bash
1. 模拟 FTS5 不可用（禁用 fts5 扩展或覆盖 capability check）
2. GET /api/v1/memory/search?q=测试
   → 返回 200 + LIKE 搜索结果（不报 500）
3. POST /api/v1/memory/recall
   Body: {"goal_summary": "测试"}
   → 返回 200 + 结果（不报 500）
4. 恢复 FTS5 → 自动切回 FTS5 搜索
```

---

## 依赖与前置条件

| # | 依赖 | 状态 | 影响 |
|:-:|:-----|:----:|:-----|
| 1 | v0.2 Learning Candidate 表 | ✅ | 数据源 |
| 2 | v0.3 CEO Skill | ✅ | 需要增强 |
| 3 | FTS5 在 SQLite 中可用 | ✅ | Python sqlite3 默认支持 |
| 4 | 后端 8001 | ✅ | — |
| 5 | 前端 3001 | ✅ | — |

---

## 风险

| 风险 | 影响 | 缓解 |
|:-----|:------|:------|
| FTS5 trigger 维护成本 | 数据不同步 | 使用 SQLAlchemy event 监听替代 |
| Knowledge Proposal 自动生成质量差 | 需要大量修改 | 半自动 + Founder 确认，可 revise |
| 来源链查询复杂（多表 JOIN） | 页面加载慢 | 单独做来源链缓存字段 |
