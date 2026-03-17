# Contracts: Python Skills

**Feature**: File System Watcher (Bronze P1)
**Date**: 2026-03-07
**Branch**: 001-file-system-watcher

---

## Skills Contract

### `create_action_file()`

**Purpose**: Create an action file in `vault/Needs_Action/` with proper metadata and audit logging.

**Signature**:
```python
def create_action_file(
    file_type: str,
    source: str,
    content: str = "",
    dry_run: bool = False
) -> str:
    """
    Create action file in Needs_Action/ with metadata.
    
    Args:
        file_type: Type of action ('file_drop', 'email', 'approval_request')
        source: Relative path to source file (e.g., 'Inbox/test.txt')
        content: Optional content to include in action file
        dry_run: If True, log intended action without creating file
        
    Returns:
        Path to created file (or would-be path if dry_run)
        
    Raises:
        ValueError: If file_type is invalid or source path is malformed
        PermissionError: If cannot write to Needs_Action/ directory
        OSError: If disk is full or other system error occurs
    """
```

**Inputs**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| file_type | str | Yes | MUST be one of: `file_drop`, `email`, `approval_request` |
| source | str | Yes | MUST be relative path within vault (no absolute paths) |
| content | str | No | Optional markdown content for action file body |
| dry_run | bool | No | Default: `False` - if True, log only, don't create file |

**Outputs**:
| Return Type | Description |
|-------------|-------------|
| str | Absolute path to created action file (or would-be path if dry_run) |

**Error Taxonomy**:
| Error | Condition | Handling |
|-------|-----------|----------|
| `ValueError` | Invalid file_type or malformed source path | Log ERROR, raise to caller |
| `PermissionError` | Cannot write to Needs_Action/ | Log ERROR with stack trace, raise to caller |
| `OSError` (errno 28) | Disk full | Log CRITICAL, create alert file, raise to caller |
| `OSError` (other) | Other system errors | Log ERROR with stack trace, raise to caller |

**Example Usage**:
```python
# Normal usage
path = create_action_file(
    file_type='file_drop',
    source='Inbox/test.txt',
    content='File dropped for processing.'
)
# Returns: 'H:\\...\\Needs_Action\\FILE_test_20260307103000.md'

# Dry-run mode
path = create_action_file(
    file_type='file_drop',
    source='Inbox/test.txt',
    dry_run=True
)
# Returns: 'H:\\...\\Needs_Action\\FILE_test_20260307103000.md' (would-be path)
# No file is created, only logged
```

**Action File Format**:
```markdown
---
type: {file_type}
source: {source}
created: {ISO-8601 timestamp}
status: pending
---

## Content
{content}

## Suggested Actions
- [ ] Process this file
- [ ] Move to Done when complete
```

---

### `log_audit()`

**Purpose**: Write an audit log entry to `vault/Logs/audit_YYYY-MM-DD.jsonl`.

**Signature**:
```python
def log_audit(
    action: str,
    details: dict,
    level: str = "INFO",
    component: str = "skills",
    dry_run: bool = False
) -> None:
    """
    Write audit log entry to vault/Logs/.
    
    Args:
        action: Action type ('file_created', 'action_executed', 'error', etc.)
        details: Dictionary with contextual data
        level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        component: Component name ('skills', 'filesystem_watcher', 'audit_logger')
        dry_run: If True, log to stdout instead of file
        
    Raises:
        ValueError: If level is invalid or details is not a dict
        PermissionError: If cannot write to Logs/ directory
        OSError: If disk is full or other system error occurs
    """
```

**Inputs**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| action | str | Yes | MUST be one of: `file_created`, `action_executed`, `error`, `halt`, `dry_run` |
| details | dict | Yes | MUST be a dictionary with contextual data |
| level | str | No | Default: `INFO` - MUST be one of: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| component | str | No | Default: `skills` - Component name |
| dry_run | bool | No | Default: `False` - if True, log to stdout instead of file |

**Outputs**:
| Return Type | Description |
|-------------|-------------|
| None | Writes to log file (or stdout if dry_run) |

**Error Taxonomy**:
| Error | Condition | Handling |
|-------|-----------|----------|
| `ValueError` | Invalid level or details not dict | Log ERROR to stderr, raise to caller |
| `PermissionError` | Cannot write to Logs/ | Log ERROR to stderr with stack trace, raise to caller |
| `OSError` (errno 28) | Disk full | Log CRITICAL to stderr, create alert file, raise to caller |
| `OSError` (other) | Other system errors | Log ERROR to stderr with stack trace, raise to caller |

**Log Entry Schema**:
```json
{
  "timestamp": "2026-03-07T10:30:00Z",
  "level": "INFO",
  "component": "skills",
  "action": "file_created",
  "dry_run": false,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "details": {
    "file_type": "file_drop",
    "source": "Inbox/test.txt",
    "action_file": "Needs_Action/FILE_test_20260307103000.md"
  }
}
```

**Example Usage**:
```python
# Normal usage
log_audit(
    action='file_created',
    details={
        'file_type': 'file_drop',
        'source': 'Inbox/test.txt',
        'action_file': 'Needs_Action/FILE_test_20260307103000.md'
    },
    level='INFO'
)

# Dry-run mode
log_audit(
    action='file_created',
    details={'test': 'data'},
    dry_run=True
)
# Outputs to stdout instead of file:
# {"timestamp":"2026-03-07T10:30:00Z","level":"INFO","component":"skills","action":"file_created","dry_run":true,"details":{"test":"data"}}
```

---

### `check_dev_mode()`

**Purpose**: Validate that DEV_MODE environment variable is set to "true".

**Signature**:
```python
def check_dev_mode() -> bool:
    """
    Validate DEV_MODE environment variable.
    
    Returns:
        True if DEV_MODE is set to "true"
        
    Raises:
        SystemExit: If DEV_MODE is not set or not "true"
    """
```

**Inputs**: None (reads from environment variable)

**Outputs**:
| Return Type | Description |
|-------------|-------------|
| bool | `True` if DEV_MODE is set and equals "true" |

**Error Taxonomy**:
| Error | Condition | Handling |
|-------|-----------|----------|
| `SystemExit` | DEV_MODE not set or not "true" | Log CRITICAL, exit with code 1 |

**Example Usage**:
```python
# Normal usage (DEV_MODE=true)
check_dev_mode()  # Returns: True

# Error case (DEV_MODE not set)
check_dev_mode()  # Raises: SystemExit(1)
# CRITICAL: DEV_MODE is not set to "true" (current: None)
```

---

### `validate_path()`

**Purpose**: Validate that a file path is within the vault directory (prevent path traversal).

**Signature**:
```python
def validate_path(file_path: str | Path, vault_path: str | Path) -> Path:
    """
    Validate path is within vault directory.
    
    Args:
        file_path: Path to validate
        vault_path: Base vault directory path
        
    Returns:
        Resolved absolute Path object
        
    Raises:
        ValueError: If path is not within vault (traversal attempt)
    """
```

**Inputs**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| file_path | str \| Path | Yes | Path to validate (file or directory) |
| vault_path | str \| Path | Yes | Base vault directory path |

**Outputs**:
| Return Type | Description |
|-------------|-------------|
| Path | Resolved absolute Path object (via `Path.resolve()`) |

**Error Taxonomy**:
| Error | Condition | Handling |
|-------|-----------|----------|
| `ValueError` | Path not within vault (traversal attempt) | Log ERROR, raise to caller with details |

**Example Usage**:
```python
# Valid path
vault = Path("H:\\vault")
file = Path("H:\\vault\\Inbox\\test.txt")
validated = validate_path(file, vault)
# Returns: Path("H:\\vault\\Inbox\\test.txt").resolve()

# Invalid path (traversal attempt)
file = Path("H:\\vault\\..\\..\\etc\\passwd")
validate_path(file, vault)
# Raises: ValueError("Path traversal attempt detected: H:\\etc\\passwd")
```

---

## Type Hints Summary

**All skills use Python 3.13+ type hints**:

```python
from pathlib import Path
from typing import Any

# create_action_file
def create_action_file(
    file_type: str,
    source: str,
    content: str = "",
    dry_run: bool = False
) -> str: ...

# log_audit
def log_audit(
    action: str,
    details: dict[str, Any],
    level: str = "INFO",
    component: str = "skills",
    dry_run: bool = False
) -> None: ...

# check_dev_mode
def check_dev_mode() -> bool: ...

# validate_path
def validate_path(file_path: str | Path, vault_path: str | Path) -> Path: ...
```

---

## Testing Contract

**Contract Tests** (in `tests/contract/test_skills_contract.py`):

```python
def test_create_action_file_signature():
    """Verify create_action_file has correct signature."""
    sig = inspect.signature(create_action_file)
    params = list(sig.parameters.keys())
    assert params == ['file_type', 'source', 'content', 'dry_run']
    
def test_create_action_file_return_type():
    """Verify create_action_file returns str."""
    result = create_action_file('file_drop', 'Inbox/test.txt', dry_run=True)
    assert isinstance(result, str)
    
def test_log_audit_signature():
    """Verify log_audit has correct signature."""
    sig = inspect.signature(log_audit)
    params = list(sig.parameters.keys())
    assert params == ['action', 'details', 'level', 'component', 'dry_run']
    
def test_check_dev_mode_returns_bool():
    """Verify check_dev_mode returns bool."""
    os.environ['DEV_MODE'] = 'true'
    result = check_dev_mode()
    assert isinstance(result, bool)
    assert result is True
    
def test_validate_path_returns_path():
    """Verify validate_path returns Path."""
    result = validate_path('Inbox/test.txt', './vault')
    assert isinstance(result, Path)
```

---

**Version**: 1.0 | **Status**: Approved | **Next**: quickstart.md
