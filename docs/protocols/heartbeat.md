# Heartbeat Protocol

**Purpose**: Define how the system continuously self-checks, self-advances, and avoids complete dependence on manual triggers.

## Why It Exists

Early system required manual triggers for every action. Human had to be present to run tasks.

Heartbeat enables autonomous operation: system checks itself, runs scheduled tasks, reports status without human intervention.

## Key Mechanism

```
Heartbeat Trigger (cron 09:00 / 18:00)
  → Scan Active Projects
    → Check Task Queue
      → Dispatch Waiting Tasks
        → Update Execution Records
          → Generate Reports
```

## How It's Used

1. **Scheduled Trigger**: Runs automatically at configured times (09:00, 18:00)
2. **Project Scan**: Checks which projects need attention
3. **Task Dispatch**: Routes waiting tasks to appropriate agents
4. **Record Update**: Updates execution-records.json
5. **Report Generation**: Creates daily/weekly reports

## Example / Application

**Daily Heartbeat (09:00)**:
- Scan: novel-v1, research-agent
- Check: Are there tasks to run today?
- Dispatch: If yesterday incomplete, resume; if new, start
- Report: Log to heartbeat.log

**Evening Heartbeat (18:00)**:
- Scan: All active projects
- Report: Generate Daily Report
- Alert: Flag any blocked tasks

## Current Limitations

- Fixed schedule (not event-driven)
- Some tasks still require manual trigger
- Alerting not fully automated

## Next Evolution

- Event-driven triggers (not just time-based)
- More autonomous decision-making
- Predictive scheduling based on task patterns
