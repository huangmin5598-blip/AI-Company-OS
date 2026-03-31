# Failure Protocol

**Purpose**: Define how the system identifies failures, records them, processes them, and converts failures into reusable learnings.

## Why It Exists

Failure is inevitable. What matters is how system responds. Without failure protocol: failures were ignored, repeated, or lost.

Failure Protocol ensures every failure is captured, handled, and used to improve the system.

## Key Mechanism

```
Failure Detected
  → Classify Failure Type
    → Determine Recovery Strategy
      → Execute Recovery (fallback/resume/main_rescue)
        → Record in Execution Records
          → Update Autonomy Status
```

## How It's Used

1. **Detection**: Timeout, error, or manual flag triggers failure detection
2. **Classification**: What's the failure type? (timeout, error, blocked)
3. **Strategy Selection**: Which recovery path?
   - fallback: retry with backup agent
   - resume: continue from checkpoint
   - main_rescue: human/AI intervention
4. **Recovery Execution**: Execute the chosen strategy
5. **Recording**: Log failure in execution-records.json
6. **Status Update**: Mark autonomy_status (resumed/main_rescue)

## Example / Application

**Writer timeout scenario**:
- Detection: writer doesn't respond after 8min
- Classification: timeout
- Strategy: Check for checkpoint → found structure checkpoint
- Recovery: resume_from_checkpoint
- Recording: task marked as "resumed"
- Result: Task completed successfully

## Current Limitations

- Not all failure types handled
- Some edge cases still cause system hang
- Failure pattern analysis not yet implemented

## Next Evolution

- Automated failure pattern detection
- Predictive failure prevention
- Learning from failures to improve routing
