# Production Protocol

**Purpose**: Define how the system transforms task triggers into stable outputs, forming a unified production standard.

## Why It Exists

Early system ran tasks ad-hoc. Each task was different. No standard process. No predictability.

Production Protocol establishes a standard path from task definition to output delivery.

## Key Mechanism

```
task_created 
  → task_dispatched_to_agent 
    → agent_executes 
      → quality_gate (PASS/REVISION)
        → output_exported 
          → asset_registered
```

## How It's Used

1. **Task Creation**: Lead creates Task Card with required fields
2. **Dispatch**: Task routed to appropriate agent based on capability
3. **Execution**: Agent produces output
4. **Quality Gate**: Review agent checks quality
5. **Export**: Output converted to persistent format
6. **Registration**: Asset recorded in registry

## Example / Application

**novel-v1 daily production**:
- Task: "Write 2 novels today"
- Dispatch: lead-novel → story → writer → review → export
- Output: 2 docx files in manuscripts/
- Registration: Both recorded in execution-records.json

## Current Limitations

- Not all projects follow full pipeline
- Export formats not standardized across all types
- Quality gates need more defined criteria

## Next Evolution

- Add automated quality metrics
- Standardize export formats across all projects
- Add automated progress tracking
