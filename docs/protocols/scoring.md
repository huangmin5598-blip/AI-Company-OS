# Project Scoring System

**Purpose**: Define how projects and opportunities are evaluated before launch, to avoid building blindly.

## Why It Exists

Not every idea should become a project. Without evaluation: resources wasted on low-potential ideas.

Scoring System provides structured evaluation criteria before committing resources.

## Key Mechanism

```
Opportunity Identified
  → Score on Multiple Dimensions
    → Calculate Total Score
      → Decide: Build / Wait / Drop
```

## How It's Used

1. **Identification**: Opportunity or idea emerges
2. **Multi-Dimensional Scoring**: Rate on key factors
3. **Total Score Calculation**: Weighted sum or composite
4. **Decision**: Based on threshold or comparison

## Scoring Dimensions

| Dimension | Weight | Factors |
|-----------|--------|----------|
| Pain | 20% | How strong is the pain point? |
| Monetization | 20% | Clear revenue path? |
| MVP Feasibility | 20% | Can we ship fast? |
| Speed | 15% | Time to first output? |
| Competition | 15% | How crowded is the space? |
| Strategic Fit | 10% | Aligns with goals? |

## Example / Application

**Opportunity: 小微企业AI工作流自动化工具**

| Dimension | Score (1-10) | Weight | Contribution |
|-----------|--------------|--------|--------------|
| Pain | 8 | 20% | 1.6 |
| Monetization | 7 | 20% | 1.4 |
| MVP Feasibility | 9 | 20% | 1.8 |
| Speed | 8 | 15% | 1.2 |
| Competition | 6 | 15% | 0.9 |
| Strategic Fit | 7 | 10% | 0.7 |
| **Total** | | | **7.6 / 10** |

**Decision**: Build (score > 6)

## Current Limitations

- Subjective scoring (depends on evaluator)
- Weights not fully validated
- Not integrated into automated decision flow

## Next Evolution

- Automated data-driven scoring (market data)
- Historical score validation against outcomes
- Integration with project initiation workflow
