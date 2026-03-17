# Company Handbook

## Rules of Engagement

### Security Rules
1. Always check DEV_MODE before any action
2. Always respect --dry-run flag
3. Never access files outside vault/
4. Always log all actions to /Logs/

### Escalation Rules
1. Payment-related actions → Require human approval
2. External API calls → Require human approval
3. File deletions → Require human approval
4. Any action with uncertainty → Create approval request

### Contact Priority
1. Critical errors → Create alert file in Needs_Action/
2. Questions → Log and continue
3. Completion → Move to Done/ and log

## Emergency Procedures
- To stop all operations: Create `vault/STOP` file
- To review audit trail: Check `vault/Logs/`
