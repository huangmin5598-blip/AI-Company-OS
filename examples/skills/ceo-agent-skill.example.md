# CEO Agent Skill — Example

> **Hermes skill for AI Company OS CEO Agent integration.**
> This is an example file. The actual skill is deployed locally.

## Purpose

The CEO Agent skill allows Hermes to act as the CEO Agent in AI Company OS:

1. **Goal Intake**: Accept founder's natural language goal → decompose into structured tasks → write to company loop
2. **Approval Action**: Parse founder's natural language approval → call approval API → audit log

## Key Workflows

### Workflow 1: Goal Intake

```
Founder: "We need to expand into the short drama market"

CEO Agent:
1. POST /ceo/commit-decomposition
   → Creates goal_session record
   → Generates 3-5 tasks in task_pool
   → Creates context_packs per task
   → Creates approval requests
2. Returns: "Created goal session 'Short drama market expansion' with 4 tasks pending your approval"
```

### Workflow 2: Approval Action

```
Founder: "Approve task 3 about market research"

CEO Agent:
1. GET /approvals?search=market+research
2. Matches approval ID
3. PATCH /approvals/{id} → "approved"
4. Returns: "Approved: Market research project (approval #42)"
```

## Integration

The skill integrates with:
- `goal_sessions` API
- `approvals` API
- `memory_recall` API (pre-fetches org memory before goal intake)
- Context Pack builder with `referenced_memory_ids`

See `docs/prd/` for full PRDs and API specifications.
