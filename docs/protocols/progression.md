# Progression Protocol

**Purpose**: Define how the system advances from single execution to continuous progression and autonomous growth.

## Why It Exists

Single task execution is not enough. System needs to progress on its own — not waiting for manual commands, but advancing tasks through stages automatically.

Progression Protocol defines how the system moves tasks forward without constant human nudging.

## Key Mechanism

```
Task Completed
  → Check Next Stage
    → Auto-dispatch to Next Agent
      → Monitor Progress
        → On Completion, Repeat
```

## How It's Used

1. **Completion Detection**: When task triggers task_completed_event
2. **Next Stage Lookup**: Check what comes next in pipeline
3. **Auto-dispatch**: Route to next agent automatically
4. **Progress Monitoring**: Track that task is advancing
5. **Loop**: Repeat until pipeline complete

## Example / Application

**novel-v1 pipeline progression**:
- Writer completes chapter → task_completed_event
- System checks: next is review-editor
- Auto-dispatch: task sent to review-editor
- Review completes → export → asset registered
- System ready for next task

## Current Limitations

- Not all pipelines fully automated
- Some stages require manual dispatch
- Progress tracking not comprehensive

## Next Evolution

- Fully automated pipeline progression
- Cross-project dependency handling
- Self-optimizing based on completion rates
