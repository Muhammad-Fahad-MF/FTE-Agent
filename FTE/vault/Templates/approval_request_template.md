---
type: approval_request
action: {{ACTION_TYPE}}
action_details: {{ACTION_DETAILS}}
created: {{CREATED_DATE}}
expires: {{EXPIRES_DATE}}
status: pending
risk_level: {{RISK_LEVEL}}
reason: {{REASON}}
---

# Approval Request: {{ACTION_TYPE}}

## Request Details

| Field | Value |
|-------|-------|
| **Action Type** | {{ACTION_TYPE}} |
| **Created** | {{CREATED_DATE}} |
| **Expires** | {{EXPIRES_DATE}} (24 hours from creation) |
| **Risk Level** | {{RISK_LEVEL}} |
| **Status** | ⏳ Pending |

## Reason for Approval

{{REASON}}

## Action Details

{{ACTION_DETAILS}}

## Decision

**Instructions:**
- To **APPROVE**: Change `status: pending` to `status: approved` and save
- To **REJECT**: Change `status: pending` to `status: rejected` and add reason below
- Approval expires after 24 hours (see `expires` field)

---

### Approval Record

| Decision | Date | Authorized By | Notes |
|----------|------|---------------|-------|
| ⏳ Pending | - | - | Awaiting user decision |

**Rejection Reason** (if applicable):

{{REJECTION_REASON}}

---

**Metadata:**
- File: `vault/Pending_Approval/APPROVAL_{{TIMESTAMP}}.md`
- Correlation ID: `{{CORRELATION_ID}}`
- Source: {{SOURCE_FILE}}
