# 🌐 Gateway Summary — AI Company OS

**Version**: 1.0 (External Preview)
**Updated**: 2026-04-01
**Data Date**: 2026-03-30
**Purpose**: External display / GitHub / Landing page

---

## 今日概览

| 指标 | 值 |
|------|-----|
| **Total Calls** | 8 |
| **Total Cost** | $0.00255 |
| **Fallback** | 2 次 |
| **Success Rate** | 100% |

---

## 调用详情

| # | Agent | Provider | Model | Cost | Status | Fallback |
|---|-------|----------|-------|------|--------|----------|
| 1 | finance-analyst | minimax-cn | MiniMax-M2.5 | $0.00038 | ✅ success | - |
| 2 | research-agent | minimax-cn | MiniMax-M2.5 | $0.00050 | ✅ success | - |
| 3 | lead-novel | minimax-cn | MiniMax-M2.5 | $0.00041 | ✅ success | - |
| 4 | research-agent | ollama | deepseek-r1:8b | $0.00 | ✅ success | ⚠️ timeout |
| 5 | story-editor | minimax-cn | MiniMax-M2.5 | $0.00043 | ✅ success | - |
| 6 | writer | minimax-cn | MiniMax-M2.5 | $0.00043 | ✅ success | - |
| 7 | review-editor | minimax-cn | MiniMax-M2.5 | $0.00040 | ✅ success | - |
| 8 | story-editor | ollama | deepseek-r1:8b | $0.00 | ✅ success | ⚠️ timeout |

---

## Agent 成本 TOP

| # | Agent | Cost (USD) | Calls |
|---|-------|------------|-------|
| 1 | research-agent | $0.00050 | 2 |
| 2 | story-editor | $0.00043 | 2 |
| 3 | writer | $0.00043 | 1 |
| 4 | review-editor | $0.00040 | 1 |
| 5 | lead-novel | $0.00041 | 1 |
| 6 | finance-analyst | $0.00038 | 1 |

---

## Fallback 分析

| 触发次数 | 原因 | 处理方式 |
|----------|------|----------|
| 2 | timeout | 自动切换到 Ollama (deepseek-r1:8b) |

**Fallback 机制**:
- 当主模型超时 → 自动切换到本地 Ollama 模型
- 本地模型成本 = $0.00
- 保证服务可用性

---

## Provider 分布

| Provider | Calls | Cost | Fallback |
|----------|-------|------|----------|
| minimax-cn | 6 | $0.00255 | 0 |
| ollama (本地) | 2 | $0.00 | 2 |

---

## 成本趋势 (周度)

| Week | Total Cost | Change |
|------|------------|--------|
| Week 12 | $0.01200 | - |
| Week 13 | $0.01500 | +25% |
| Week 14 | $0.01650 | +10% |
| Week 15 (proj.) | $0.01800 | +9% |

---

## 治理规则

### Fallback 策略
1. **Primary**: MiniMax-M2.5 (云端)
2. **Fallback**: Ollama deepseek-r1:8b (本地)
3. **触发条件**: timeout > 30s
4. **恢复**: 自动切换

### 成本警告
- 阈值: $0.01/day
- 当前: $0.00255 ✅ 正常

---

## Gateway 配置

| 配置项 | 值 |
|--------|-----|
| **Port** | 18789 |
| **Bind** | 127.0.0.1 (loopback) |
| **Primary Model** | MiniMax-M2.5 |
| **Fallback Model** | Ollama deepseek-r1:8b |
| **Timeout** | 30s |
| **Cost Alert** | $0.01/day |

---

## 数据来源

- `gateway-lite/daily/2026-03-30.json` → 调用记录
- `gateway-lite/OPERATIONS.md` → 运营配置

---

*Generated: 2026-04-01 04:07 (Asia/Shanghai)*