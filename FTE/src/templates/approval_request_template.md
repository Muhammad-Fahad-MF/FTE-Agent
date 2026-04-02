---
type: {{ action_type }}
action: {{ action_name }}
action_details:
  description: {{ action_description }}
  parameters: {{ action_parameters }}
  risk_level: {{ risk_level }}
created: {{ created_timestamp }}
expires: {{ expiry_timestamp }}
status: pending
risk_level: {{ risk_level }}
approved_by: null
approved_at: null
---

# Approval Request: {{ action_name }}

## Action Details

**Type**: {{ action_type }}
**Description**: {{ action_description }}
**Risk Level**: {{ risk_level }}

## Parameters

```yaml
{{ action_parameters_yaml }}
```

## Approval Timeline

- **Created**: {{ created_timestamp }}
- **Expires**: {{ expiry_timestamp }} (24 hours from creation)
- **Status**: Pending

## Approval Instructions

To approve this request:

1. Review the action details above
2. Verify the risk level is acceptable
3. Move this file to `/Vault/Approved/` to approve
4. Or move to `/Vault/Rejected/` to reject

## Notes

Add any comments or considerations below:

---

## Approval Decision

**Decision**: [ ] Approved [ ] Rejected

**Approved By**: _______________

**Approved At**: _______________

**Comments**:

