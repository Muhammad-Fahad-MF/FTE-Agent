# Quickstart: File System Watcher

**Feature**: File System Watcher (Bronze P1)
**Date**: 2026-03-07
**Branch**: 001-file-system-watcher

---

## Prerequisites

### System Requirements
- **Python**: 3.13+ (verify: `python --version`)
- **uv**: Latest (verify: `uv --version`)
- **Git**: Latest (verify: `git --version`)

### Environment Setup

1. **Install dependencies**:
   ```bash
   cd H:\Programming\FTE-Agent
   uv sync
   ```

2. **Create vault structure**:
   ```bash
   mkdir vault\Inbox
   mkdir vault\Needs_Action
   mkdir vault\Done
   mkdir vault\Logs
   mkdir vault\Pending_Approval
   mkdir vault\Approved
   mkdir vault\Rejected
   ```

3. **Configure environment**:
   ```bash
   # Create .env file
   echo DEV_MODE=true > .env
   echo DRY_RUN=true >> .env
   echo VAULT_PATH=H:\Programming\FTE-Agent\vault >> .env
   ```

4. **Verify .gitignore**:
   ```bash
   # Should show .env is ignored
   git check-ignore .env
   ```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| DEV_MODE | Yes | - | Must be "true" to run (security kill switch) |
| DRY_RUN | No | false | If "true", log without executing |
| VAULT_PATH | No | ./vault | Path to Obsidian vault |
| WATCHER_INTERVAL | No | 60 | Check interval in seconds (max 60) |

### CLI Flags

```bash
# Basic usage (uses env vars or defaults)
python -m src.filesystem_watcher

# Custom vault path
python -m src.filesystem_watcher --vault-path /path/to/vault

# Dry-run mode
python -m src.filesystem_watcher --dry-run

# Custom interval
python -m src.filesystem_watcher --interval 30

# Combined
python -m src.filesystem_watcher --vault-path /path/to/vault --dry-run --interval 30
```

### Precedence

CLI flags > Environment variables > Defaults

Example:
```bash
# Env says dry-run=false, CLI says --dry-run
# Result: dry-run is enabled (CLI wins)
set DRY_RUN=false
python -m src.filesystem_watcher --dry-run
```

---

## Validation Scenarios

### Scenario 1: Happy Path - File Detection to Action Creation

**Goal**: Verify that dropping a file in Inbox/ creates an action file in Needs_Action/.

**Steps**:
1. Start the watcher in dry-run mode:
   ```bash
   python src/filesystem_watcher.py --dry-run --interval 10
   ```

2. In a new terminal, create a test file:
   ```bash
   echo "test content" > vault\Inbox\test1.txt
   ```

3. Wait 10-15 seconds for watcher to detect.

4. **Expected Output** (watcher terminal):
   ```
   INFO: file_detected - vault\Inbox\test1.txt
   INFO: [DRY-RUN] Would create action file: vault\Needs_Action\FILE_test1_20260307103000.md
   ```

5. **Verify**:
   - No action file created (dry-run mode)
   - Log entry in `vault\Logs\audit_YYYY-MM-DD.jsonl`

**Automated Test**:
```bash
python -m pytest tests/integration/test_watcher_to_action.py::test_file_detected_to_action_created -v
```

---

### Scenario 2: Edge Case - File Size Boundary (10MB)

**Goal**: Verify that files exactly 10MB are processed, but files >10MB are skipped.

**Steps**:
1. Create a 10MB file (boundary):
   ```bash
   python -c "open('vault/Inbox/test_10mb.txt', 'wb').write(b'x' * 10485760)"
   ```

2. Create a 10.1MB file (over limit):
   ```bash
   python -c "open('vault/Inbox/test_over_10mb.txt', 'wb').write(b'x' * 10590000)"
   ```

3. Run watcher:
   ```bash
   python src/filesystem_watcher.py --dry-run --interval 10
   ```

4. **Expected Output**:
   ```
   INFO: file_detected - vault\Inbox\test_10mb.txt
   INFO: [DRY-RUN] Would create action file: vault\Needs_Action\FILE_test_10mb_...md
   WARNING: File too large (>10MB): vault\Inbox\test_over_10mb.txt (10590000 bytes)
   ```

**Automated Test**:
```bash
python -m pytest tests/unit/test_filesystem_watcher.py::test_file_size_boundary -v
```

---

### Scenario 3: Error Handling - Permission Denied

**Goal**: Verify that permission errors are logged and watcher continues.

**Steps**:
1. Create a read-only file:
   ```bash
   echo "readonly" > vault\Inbox\readonly.txt
   icacls vault\Inbox\readonly.txt /deny Everyone:R  # Windows
   # or: chmod 000 vault/Inbox/readonly.txt  # Linux/macOS
   ```

2. Run watcher:
   ```bash
   python src/filesystem_watcher.py --dry-run --interval 10
   ```

3. **Expected Output**:
   ```
   ERROR: Permission denied: vault\Inbox\readonly.txt
   Traceback (most recent call last):
     File "src/filesystem_watcher.py", line ..., in ...
   PermissionError: [Errno 13] Permission denied: 'vault\\Inbox\\readonly.txt'
   INFO: Continuing monitoring...
   ```

4. **Verify**: Watcher continues running (doesn't crash)

**Automated Test**:
```bash
python -m pytest tests/unit/test_filesystem_watcher.py::test_permission_error_handling -v
```

---

### Scenario 4: Security - Path Traversal Attempt

**Goal**: Verify that path traversal attacks are detected and rejected.

**Steps**:
1. Attempt to create a file with traversal path (simulated):
   ```bash
   # This is a test - don't actually create the file
   # Test validates that IF a file like ../../etc/passwd was detected, it would be rejected
   ```

2. Run unit test:
   ```bash
   python -m pytest tests/unit/test_filesystem_watcher.py::test_path_validation_traversal_attempt -v
   ```

3. **Expected Output**:
   ```
   PASSED: test_path_validation_traversal_attempt
   ```

**Manual Verification** (if needed):
```python
from pathlib import Path
from src.filesystem_watcher import validate_path

try:
    validate_path("../../etc/passwd", "./vault")
    print("FAIL: Should have raised ValueError")
except ValueError as e:
    print(f"PASS: {e}")
```

---

### Scenario 5: STOP File - Emergency Halt

**Goal**: Verify that creating vault/STOP halts the watcher.

**Steps**:
1. Start watcher:
   ```bash
   python src/filesystem_watcher.py --interval 5
   ```

2. Wait 10 seconds for watcher to start.

3. Create STOP file:
   ```bash
   touch vault\STOP
   ```

4. **Expected Output** (within 60 seconds):
   ```
   WARNING: STOP file detected - halting watcher
   INFO: Cleanup complete
   INFO: Watcher stopped
   ```

5. **Verify**: Watcher process has exited

**Automated Test**:
```bash
python -m pytest tests/unit/test_filesystem_watcher.py::test_stop_file_detection -v
```

---

### Scenario 6: DEV_MODE Validation

**Goal**: Verify that watcher exits if DEV_MODE is not set.

**Steps**:
1. Unset DEV_MODE:
   ```bash
   set DEV_MODE=  # Windows
   # or: unset DEV_MODE  # Linux/macOS
   ```

2. Run watcher:
   ```bash
   python src/filesystem_watcher.py
   ```

3. **Expected Output**:
   ```
   CRITICAL: DEV_MODE is not set to "true" (current: None or '')
   SystemExit: 1
   ```

**Automated Test**:
```bash
python -m pytest tests/unit/test_filesystem_watcher.py::test_dev_mode_validation -v
```

---

## Automated Test Commands

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Unit Tests
```bash
python -m pytest tests/unit/ -v
```

### Run Integration Tests
```bash
python -m pytest tests/integration/ -v
```

### Run Contract Tests
```bash
python -m pytest tests/contract/ -v
```

### Run Chaos Tests
```bash
python -m pytest tests/chaos/ -v
```

### Run with Coverage
```bash
python -m pytest --cov=src --cov-report=term-missing --cov-report=html
```

### Verify Coverage Threshold (80%+)
```bash
python -m pytest --cov=src --cov-fail-under=80
```

---

## Quality Gates

### Linting (ruff)
```bash
ruff check src/ tests/
# Expected: 0 errors
```

### Formatting (black)
```bash
black --check src/ tests/
# Expected: All files formatted correctly
```

### Type Checking (mypy)
```bash
mypy --strict src/ tests/
# Expected: 0 errors
```

### Security Scan (bandit)
```bash
bandit -r src/ tests/
# Expected: 0 high-severity issues
```

### Import Order (isort)
```bash
isort --check src/ tests/
# Expected: All imports sorted correctly
```

---

## Manual Testing Checklist

### Core Functionality
- [ ] File dropped in Inbox/ creates action file in Needs_Action/
- [ ] Action file contains correct metadata (type, source, created, status)
- [ ] --dry-run flag prevents file creation (logs only)
- [ ] DEV_MODE validation exits if not "true"
- [ ] STOP file halts watcher within 60 seconds

### Error Handling
- [ ] PermissionError is logged and watcher continues
- [ ] FileNotFoundError is logged and added to retry queue
- [ ] DiskFullError halts watcher gracefully
- [ ] Path traversal attempts are rejected

### Observability
- [ ] All actions logged to vault/Logs/audit_YYYY-MM-DD.jsonl
- [ ] Log entries contain all required fields (timestamp, level, component, action, dry_run, correlation_id, details)
- [ ] Log rotation works (7 days or 100MB)
- [ ] Error logs include full stack traces

### Security
- [ ] All paths validated to start with vault_path
- [ ] No files created outside vault/
- [ ] .env file excluded from git
- [ ] No secrets logged

### Performance
- [ ] File detection latency <60 seconds
- [ ] Action file creation <2 seconds for files <10MB
- [ ] Memory usage <100MB
- [ ] CPU usage <5%

---

## Runbooks

### Runbook 1: Watcher Not Detecting Files

**Symptoms**:
- Files dropped in Inbox/ are not detected
- No action files created
- No log entries

**Diagnosis Steps**:
1. Check watcher is running:
   ```bash
   tasklist | findstr python  # Windows
   # or: ps aux | grep python  # Linux/macOS
   ```

2. Check vault/Inbox/ exists:
   ```bash
   dir vault\Inbox  # Windows
   # or: ls vault/Inbox  # Linux/macOS
   ```

3. Check DEV_MODE is set:
   ```bash
   echo %DEV_MODE%  # Windows
   # or: echo $DEV_MODE  # Linux/macOS
   ```

4. Check logs for errors:
   ```bash
   tail vault\Logs\audit_*.jsonl  # Last 10 lines
   ```

5. Check STOP file exists:
   ```bash
   dir vault\STOP  # Windows
   # or: ls vault/STOP  # Linux/macOS
   ```

**Resolution**:
1. If watcher not running: `python src/filesystem_watcher.py`
2. If DEV_MODE not set: `echo DEV_MODE=true > .env`
3. If STOP file exists: `del vault\STOP` (Windows) or `rm vault/STOP` (Linux/macOS)
4. Restart watcher after fixes

---

### Runbook 2: Action Files Not Created

**Symptoms**:
- Files detected in Inbox/
- No action files in Needs_Action/
- Log shows "file_detected" but not "action_created"

**Diagnosis Steps**:
1. Check --dry-run mode:
   ```bash
   echo %DRY_RUN%  # Windows
   # or: echo $DRY_RUN  # Linux/macOS
   ```

2. Check vault/Needs_Action/ exists and is writable:
   ```bash
   dir vault\Needs_Action  # Windows
   # or: ls vault/Needs_Action  # Linux/macOS
   ```

3. Check logs for errors:
   ```bash
   grep "action_created" vault\Logs\audit_*.jsonl
   # Should show entries if files created
   ```

4. Check for PermissionError in logs:
   ```bash
   grep "PermissionError" vault\Logs\audit_*.jsonl
   ```

**Resolution**:
1. If --dry-run=true: Set `DRY_RUN=false` in .env
2. If Needs_Action/ doesn't exist: `mkdir vault\Needs_Action`
3. If PermissionError: Check directory permissions
4. Restart watcher after fixes

---

### Runbook 3: Log Files Growing Unbounded

**Symptoms**:
- vault/Logs/ directory using >500MB disk space
- Multiple audit_*.jsonl files not rotating
- Disk space warnings

**Diagnosis Steps**:
1. Check log file sizes:
   ```bash
   dir vault\Logs\*.jsonl  # Windows
   # or: ls -lh vault/Logs/*.jsonl  # Linux/macOS
   ```

2. Check log rotation code:
   ```bash
   grep -n "rotate_logs" src/audit_logger.py
   ```

3. Check for archived logs:
   ```bash
   dir vault\Logs\*.archived  # Windows
   # or: ls vault/Logs/*.archived  # Linux/macOS
   ```

**Resolution**:
1. Manually rotate large logs:
   ```bash
   # Rename current log
   move vault\Logs\audit_2026-03-07.jsonl vault\Logs\audit_2026-03-07.jsonl.archived
   ```

2. Delete old archived logs (keep last 7):
   ```bash
   # List archived logs by date
   dir vault\Logs\*.archived /O:D
   # Delete oldest (keep last 7)
   ```

3. Verify rotation code is working:
   ```bash
   python -c "from src.audit_logger import AuditLogger; logger = AuditLogger('test'); logger.rotate_logs()"
   ```

4. Monitor log growth after fix

---

## Troubleshooting

### Common Issues

**Issue**: Watcher exits immediately with "DEV_MODE is not set"
- **Cause**: .env file missing or DEV_MODE not set
- **Fix**: `echo DEV_MODE=true > .env` and restart watcher

**Issue**: "Permission denied" errors in logs
- **Cause**: Watcher running without read permissions on Inbox/
- **Fix**: Check directory permissions, run as appropriate user

**Issue**: Action files created with wrong metadata
- **Cause**: Bug in create_action_file() function
- **Fix**: Check function signature, verify YAML frontmatter format

**Issue**: Logs not rotating
- **Cause**: Bug in rotate_logs() or max_size_mb too high
- **Fix**: Check rotation logic, verify file size thresholds

---

**Version**: 1.0 | **Status**: Approved | **Next**: Run `/sp.tasks` to generate task breakdown
