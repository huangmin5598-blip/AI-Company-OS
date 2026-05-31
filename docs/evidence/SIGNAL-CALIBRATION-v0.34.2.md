# v0.34.2 — Signal Calibration Patch

> **日期：** 2026-05-31
> **范围：** 4 项校准补丁，不扩功能，不改 Evidence Gate 底线

---

## 变更清单

### P0 — Lineage Consistency + Candidate Idempotency

| 变更 | 文件 | 说明 |
|:-----|:-----|:------|
| Draft 来源字段补充 | `opportunity_scout.py` | Draft 尾部新增 `_source_enriched_signal` 和 `_source_note_id`，与 `_source_candidate` 形成三重追溯 |
| `source_note_id` 传入 Candidate | `opportunity_scout.py` | `enriched_to_candidate_data()` + `build_candidate()` 共同传递 |
| Candidate 幂等 | `opportunity_scout.py` | `scan-enriched` 生成前检查 `enriched_signal_ref` 是否已有 Candidate，有则 skip |

**验证：**
```
WO-DRAFT-20260531-010:
  _source_candidate: CD-20260531-002_
  _source_enriched_signal: ES-20260531-006_
  _source_note_id: SN-manual-006_
```

### P1 — signal_role 系统

| 变更 | 文件 | 说明 |
|:-----|:-----|:------|
| `signal_role` 枚举 | `enriched_signal.schema.json` | `primary_pain_signal` / `supporting_market_evidence` / `competitor_validation` / `capability_signal` / `platform_ecosystem_signal` / `internal_asset_signal` / `os_feedback_signal` / `weak_signal` |
| `determine_signal_role()` | `opportunity_enricher.py` | 根据 `source_category` + `pain.evidence_status` 自动分类 |
| `signal_role` 过滤 | `opportunity_scout.py` | `scan-enriched` 只处理 `primary_pain_signal` |

**核心规则：**
- `supporting_market_evidence` / `competitor_validation` → 不单独生成 Candidate
- `capability_signal` → 可进入 deep research 或 supporting evidence
- `weak_signal` → 默认不进入 Candidate

### P2 — Supporting Evidence 关联字段

| 变更 | 文件 | 说明 |
|:-----|:-----|:------|
| `supports_candidate_id` | Schema | 引用所支持的 Candidate |
| `supports_opportunity_id` | Schema | 引用所支持的 Opportunity |
| `supports_product_line` | Schema | 所支持的产品线 |
| `related_signal_ids` | Schema | 关联信号 ID 列表 |
| `supporting_evidence_refs` | Schema | 支持证据引用列表 |

### P3 — 中文 why_now 词表

| 变更 | 说明 |
|:-----|:------|
| ~30 个中文 timing 关键词 | 现在、近期、今年、越来越、开始、已经、近年来 |
| ~10 个中文 market pressure 词 | 利润变薄、成本上涨、竞争加剧、合规压力 |
| ~8 个中文 pain/timing 词 | 人工对账困难、多币种结算、全自动化成熟 |
| ~12 个跨境财务专项词 | Settlement报告、多币种、毛利、经营分析 |

---

## 验收清单

| # | 标准 | 状态 |
|:-:|:-----|:----:|
| 1 | Candidate lineage 检查通过（CD → ES → SN → Draft） | ✅ |
| 2 | 中文 why_now 词表补充完成 | ✅ |
| 3 | signal_role 字段加入 Enriched Signal | ✅ |
| 4 | ES-005 识别为 supporting_market_evidence | ✅ |
| 5 | Supporting evidence 不单独生成 Candidate | ✅ |
| 6 | scan-enriched 幂等（同一 ES 不重复生成 CD） | ✅ |
| 7 | request-card Draft 携带三重来源字段 | ✅ |
| 8 | ES-006 → Candidate 路径不破坏 | ✅ |
