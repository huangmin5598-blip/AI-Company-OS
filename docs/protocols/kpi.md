# KPI & Bottleneck Detection System

**Purpose**: Define how to measure system output rate, completion rate, failure reasons, and identify bottleneck positions.

## Why It Exists

Without metrics: can't tell if system is improving or degrading, can't identify what's slowing things down.

KPI System provides measurable indicators of system health and performance.

## Key Mechanism

```
Metrics Collection (daily)
  → Calculate KPIs
    → Compare to Baseline
      → Identify Bottlenecks
        → Alert / Recommend
```

## How It's Used

1. **Collection**: Gather data from execution-records.json, heartbeat.log
2. **Calculation**: Compute key metrics:
   - Completion rate: tasks completed / tasks started
   - Output rate: outputs per day/week
   - Failure rate: failures / total attempts
   - Throughput: time from task_start to task_complete
3. **Comparison**: Compare to historical baseline
4. **Bottleneck Identification**: Find slowest stage or most failed agent
5. **Alert/Recommend**: Flag issues, suggest improvements

## Key Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Completion Rate | completed / total | > 90% |
| Output Rate | outputs / day | Project dependent |
| Failure Rate | failures / attempts | < 10% |
| Avg Throughput | total_time / tasks | Decreasing |

## Example / Application

**novel-v1 KPI analysis**:
- Completion Rate: 95% (target > 90%) ✅
- Output Rate: 2/day (target 2/day) ✅
- Failure Rate: 8% (target < 10%) ✅
- Avg Throughput: 4 hours (improving)

**Bottleneck**: writer stage takes 60% of total time

## Current Limitations

- Manual KPI review (not automated dashboard)
- Not all metrics tracked consistently
- Bottleneck identification still manual

## Next Evolution

- Automated KPI dashboard
- Real-time bottleneck detection
- Predictive analytics
