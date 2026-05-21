# Task Protocol

**Purpose**: Define how tasks are created, recorded, advanced, and completed, ensuring process traceability.

## Why It Exists

Without task protocol: tasks were scattered, lost track of what's running, no visibility.

Task Protocol ensures every task has identity, status, and traceable history.

## Key Mechanism

Every task must have:
- task_id (unique identifier)
- description (what to do)
- input_context (what's provided)
- acceptance_criteria (what defines done)
- output_format (what form output takes)
- current_stage (where in pipeline)
- status (WAITING/IN_PROGRESS/COMPLETED/FAILED)

## How It's Used

1. **Create**: Lead creates Task Card with required fields
2. **Record**: Task registered in TASK-POOL.md
3. **Track**: Status updated as task advances
4. **Complete**: Completion triggers task_completed_event

## Example / Application

```yaml
task_id: novel-23
description: 写作重生千金虐渣打脸第1-5章
input_context: 选题卡、人物设定、风格要求
acceptance_criteria: 20000字，章节完整，PASS审核
output_format: docx
current_stage: reviewing
status: IN_PROGRESS
```

## Current Limitations

- Manual status updates in some cases
- Not all fields mandatory for all task types
- No automated status tracking yet

## Next Evolution

- Automated status updates from agent signals
- Timeline visualization
- Dependency tracking between tasks
