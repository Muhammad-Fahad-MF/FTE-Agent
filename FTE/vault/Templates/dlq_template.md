---
original_action: {{ORIGINAL_ACTION}}
failure_reason: {{FAILURE_REASON}}
failure_count: {{FAILURE_COUNT}}
last_attempt: {{LAST_ATTEMPT}}
details: {{DETAILS}}
---

# Dead Letter Queue Entry: {{ACTION_ID}}

## Original Action

| Field | Value |
|-------|-------|
| **Action ID** | {{ACTION_ID}} |
| **Action Type** | {{ORIGINAL_ACTION}} |
| **Failure Count** | {{FAILURE_COUNT}} |
| **Last Attempt** | {{LAST_ATTEMPT}} |
| **Max Retries** | 3 (configurable) |

## Failure Information

**Reason**: {{FAILURE_REASON}}

**Details**:
```
{{DETAILS}}
```

## Reprocessing Instructions

**To manually reprocess this action:**

1. Review the failure reason above
2. Fix the underlying issue (credentials, permissions, data, etc.)
3. Move this file from `vault/Failed_Actions/` to `vault/Needs_Action/`
4. Update the status below and re-run the action

**To archive permanently:**

1. Set `status: archived` in YAML frontmatter
2. Move to `vault/Done/` with prefix `ARCHIVED_`

---

## Reprocessing History

| Attempt | Date | Result | Notes |
|---------|------|--------|-------|
| 1 | {{FIRST_ATTEMPT}} | ❌ Failed | {{FIRST_FAILURE_REASON}} |
| 2 | {{SECOND_ATTEMPT}} | ❌ Failed | {{SECOND_FAILURE_REASON}} |
| 3 | {{LAST_ATTEMPT}} | ❌ Failed | {{FAILURE_REASON}} |

---

## Original Action Metadata

```yaml
# Original action details preserved for reference
{{ORIGINAL_ACTION_METADATA}}
```

---

**Storage:**
- SQLite: `data/failed_actions.db`
- File: `vault/Failed_Actions/DLQ_{{ACTION_ID}}.md`
- Correlation ID: `{{CORRELATION_ID}}`
