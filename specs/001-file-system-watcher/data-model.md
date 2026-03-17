# Data Model: File System Watcher

**Feature**: File System Watcher (Bronze P1)
**Date**: 2026-03-07
**Branch**: 001-file-system-watcher

---

## Entities

### 1. Action File

**Purpose**: Represents a detected file requiring processing by the orchestrator.

**Location**: `vault/Needs_Action/`

**Format**: Markdown with YAML frontmatter

**Schema**:
```markdown
---
type: file_drop
source: Inbox/test.txt
created: 2026-03-07T10:30:00Z
status: pending
---

## Content
[Optional: file content or reference]

## Suggested Actions
- [ ] Process this file
- [ ] Move to Done when complete
```

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Type of action (`file_drop`, `email`, `approval_request`) |
| source | string | Yes | Relative path to source file (e.g., `Inbox/test.txt`) |
| created | ISO-8601 | Yes | Timestamp of action file creation |
| status | string | Yes | Current status (`pending`, `processing`, `completed`, `rejected`) |

**Validation Rules**:
- `type` MUST be one of: `file_drop`, `email`, `approval_request`
- `source` MUST be a relative path within vault
- `created` MUST be valid ISO-8601 format
- `status` MUST be one of: `pending`, `processing`, `completed`, `rejected`
- File name MUST follow pattern: `FILE_<original_filename>_<timestamp>.md`

**Example**:
```markdown
---
type: file_drop
source: Inbox/client_invoice.pdf
created: 2026-03-07T10:30:00Z
status: pending
---

## Content
File dropped for processing.

## Suggested Actions
- [ ] Review invoice content
- [ ] Process payment if approved
- [ ] Move to Done when complete
```

---

### 2. Audit Log Entry

**Purpose**: Structured log entry for audit trail and compliance.

**Location**: `vault/Logs/audit_YYYY-MM-DD.jsonl`

**Format**: JSONL (one JSON object per line)

**Schema**:
```json
{
  "timestamp": "2026-03-07T10:30:00Z",
  "level": "INFO",
  "component": "filesystem_watcher",
  "action": "file_detected",
  "dry_run": false,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "details": {
    "source_path": "H:\\Programming\\FTE-Agent\\vault\\Inbox\\test.txt",
    "file_size": 1024,
    "action_file": "H:\\Programming\\FTE-Agent\\vault\\Needs_Action\\FILE_test_20260307103000.md"
  }
}
```

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| timestamp | ISO-8601 | Yes | Timestamp of log entry |
| level | string | Yes | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| component | string | Yes | Component name: `filesystem_watcher`, `audit_logger`, `skills` |
| action | string | Yes | Action type: `file_detected`, `action_created`, `error`, `halt` |
| dry_run | boolean | Yes | Whether dry-run mode was enabled |
| correlation_id | UUID | No | Tracks request across components |
| details | object | Yes | Contextual data (varies by action) |

**Validation Rules**:
- `timestamp` MUST be valid ISO-8601 format
- `level` MUST be one of: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `component` MUST be one of: `filesystem_watcher`, `audit_logger`, `skills`
- `action` MUST be one of: `file_detected`, `action_created`, `error`, `halt`, `dry_run`
- `dry_run` MUST be boolean
- `correlation_id` MUST be valid UUID if present
- Each line MUST be valid JSON (JSONL format)

**Example**:
```jsonl
{"timestamp":"2026-03-07T10:30:00Z","level":"INFO","component":"filesystem_watcher","action":"file_detected","dry_run":false,"correlation_id":"550e8400-e29b-41d4-a716-446655440000","details":{"source_path":"H:\\Inbox\\test.txt","file_size":1024}}
{"timestamp":"2026-03-07T10:30:01Z","level":"INFO","component":"filesystem_watcher","action":"action_created","dry_run":false,"correlation_id":"550e8400-e29b-41d4-a716-446655440000","details":{"action_file":"H:\\Needs_Action\\FILE_test_20260307103000.md"}}
```

---

### 3. Processed File Record

**Purpose**: In-memory tracking of files already processed to prevent duplicates.

**Location**: In-memory (cleared on watcher restart)

**Format**: Python set of tuples

**Schema**:
```python
processed_files: set[tuple[str, float]] = {
    ("H:\\Inbox\\test.txt", 1678123456.789),
    ("H:\\Inbox\\invoice.pdf", 1678123457.123),
}
```

**Structure**:
- **Key**: Tuple of (file_path_str, modified_time_float)
- **Value**: Not used (set membership is the check)

**Validation Rules**:
- File path MUST be absolute path (resolved via `Path.resolve()`)
- Modified time MUST be from `file.stat().st_mtime`
- Record is cleared on watcher restart (not persistent)

**Example Usage**:
```python
def is_processed(self, file_path: Path) -> bool:
    stat = file_path.stat()
    key = (str(file_path.resolve()), stat.st_mtime)
    return key in self.processed_files

def mark_processed(self, file_path: Path):
    stat = file_path.stat()
    key = (str(file_path.resolve()), stat.st_mtime)
    self.processed_files.add(key)
```

---

### 4. STOP File

**Purpose**: Special file that signals watcher to halt all operations.

**Location**: `vault/STOP`

**Format**: Empty file (presence is the signal)

**Schema**: N/A (file existence is the signal)

**Validation Rules**:
- File MUST exist at `vault/STOP`
- File content is ignored (presence is the signal)
- Watcher MUST check every 60 seconds
- Watcher MUST halt within 60 seconds of file creation

**Example**:
```bash
# Create STOP file
touch vault/STOP

# Watcher detects and halts
if stop_file.exists():
    logger.warning("STOP file detected - halting watcher")
    break
```

---

## Data Flow

### 1. File Detection Flow

```
User drops file
      ↓
vault/Inbox/test.txt
      ↓
FileSystemWatcher detects (watchdog event)
      ↓
Validate path (starts with vault_path)
      ↓
Check if processed (path+modified_time hash)
      ↓
Check STOP file, DEV_MODE, --dry-run
      ↓
AuditLogger logs file_detected
      ↓
Create action file via Python Skills
      ↓
AuditLogger logs action_created
      ↓
vault/Needs_Action/FILE_test_<timestamp>.md
```

---

### 2. Error Handling Flow

```
Error occurs (PermissionError, FileNotFoundError, etc.)
      ↓
Catch specific exception type
      ↓
Log error with full stack trace
      ↓
Determine recovery action:
  - PermissionError → Skip file, continue monitoring
  - FileNotFoundError → Add to retry queue
  - DiskFullError → Halt gracefully, create alert file
      ↓
Continue monitoring loop (unless halt)
```

---

### 3. Log Rotation Flow

```
On each log write:
      ↓
Check current log file size
      ↓
If size > 100MB OR age > 7 days:
  1. Close current log file
  2. Rename to audit_YYYY-MM-DD.jsonl.archived
  3. Delete oldest archived (keep last 7)
  4. Open new log file
      ↓
Write log entry to current file
```

---

## State Transitions

### Action File Status

```
pending → processing → completed
                     ↘ rejected
```

**Transitions**:
- `pending` → `processing`: Orchestrator starts processing
- `processing` → `completed`: Action executed successfully
- `processing` → `rejected`: Action failed or was rejected

---

### Watcher State

```
stopped → starting → running → stopping → stopped
                   ↘ halting ↗
```

**Transitions**:
- `stopped` → `starting`: Watcher initialized
- `starting` → `running`: DEV_MODE validated, monitoring started
- `running` → `stopping`: Graceful shutdown (SIGINT/SIGTERM)
- `running` → `halting`: STOP file detected or critical error
- `stopping`/`halting` → `stopped`: Cleanup complete

---

## Validation Rules Summary

### File System Validation
| Rule | Enforcement |
|------|-------------|
| All paths within vault | `Path.resolve()` + `relative_to()` check |
| No path traversal | `os.path.commonpath()` validation |
| File size <10MB | `file.stat().st_size` check before processing |
| No duplicate processing | `processed_files` set with path+mtime hash |

### Log Validation
| Rule | Enforcement |
|------|-------------|
| Valid JSON per line | `json.loads()` validation |
| All required fields present | Dataclass with required fields |
| Valid log level | Enum validation |
| ISO-8601 timestamp | `datetime.fromisoformat()` validation |

### Action File Validation
| Rule | Enforcement |
|------|-------------|
| Valid YAML frontmatter | `yaml.safe_load()` validation |
| Required fields present | Schema validation |
| Valid status | Enum validation |
| Unique filename | Timestamp in filename |

---

**Version**: 1.0 | **Status**: Approved | **Next**: contracts/skills-contract.md
