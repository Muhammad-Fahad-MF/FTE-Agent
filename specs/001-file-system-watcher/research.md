# Research: File System Watcher

**Feature**: File System Watcher (Bronze P1)
**Date**: 2026-03-07
**Branch**: 001-file-system-watcher

---

## Technology Comparisons

### 1. File Monitoring Libraries

**Requirement**: FR-001 (detect files within 60 seconds)

#### Option 1: polling (custom implementation)
```python
import time
import os

def watch_directory(path, interval=60):
    while True:
        files = os.listdir(path)
        # Check for new files
        time.sleep(interval)
```

**Pros**:
- Simple implementation
- No external dependencies
- Works on all platforms

**Cons**:
- High CPU usage (constant polling)
- Slow detection (up to interval seconds)
- Inefficient for large directories
- No native OS integration

**Performance**: 
- CPU: ~5-10% continuous usage
- Detection latency: 30-60 seconds (with 60s interval)
- Memory: Minimal

---

#### Option 2: pyinotify (Linux inotify)
```python
import pyinotify

wm = pyinotify.WatchManager()
handler = MyEventHandler()
notifier = pyinotify.Notifier(wm, handler)
wm.add_watch('/path', pyinotify.IN_CREATE)
notifier.loop()
```

**Pros**:
- Very efficient (kernel-level events)
- Low CPU usage
- Instant detection

**Cons**:
- **Linux-only** (not cross-platform)
- Requires inotify support
- No Windows/macOS support

**Performance**:
- CPU: <1%
- Detection latency: <1 second
- Memory: Minimal

**Verdict**: ❌ **Rejected** - Not cross-platform (Bronze tier requires Windows/Linux/macOS)

---

#### Option 3: watchdog (cross-platform library)
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        print(f"File created: {event.src_path}")

observer = Observer()
observer.schedule(MyHandler(), path, recursive=False)
observer.start()
```

**Pros**:
- **Cross-platform** (Windows/Linux/macOS)
- Uses native OS APIs:
  - Windows: ReadDirectoryChangesW
  - Linux: inotify
  - macOS: FSEvents
- Well-maintained (active development, regular releases)
- Efficient (event-driven, not polling)
- Rich event types (created, modified, deleted, moved)

**Cons**:
- External dependency (but well-established)
- Slightly larger package size (~100KB)

**Performance**:
- CPU: <1% (event-driven)
- Detection latency: <1 second
- Memory: ~5-10MB

**Verdict**: ✅ **Selected** - Best balance of cross-platform support, efficiency, and maintainability

---

### 2. Log Formats

**Requirement**: Principle XI (structured logging)

#### Option 1: Plain text
```
2026-03-07T10:30:00Z INFO filesystem_watcher file_detected {"path": "Inbox/test.txt"}
```

**Pros**:
- Human-readable
- Simple to implement
- No parsing overhead

**Cons**:
- Not machine-parseable (requires regex)
- No schema enforcement
- Hard to query/filter
- Inconsistent formatting risk

**Verdict**: ❌ **Rejected** - Not suitable for automated analysis and alerting

---

#### Option 2: JSON array
```json
[
  {"timestamp": "2026-03-07T10:30:00Z", "level": "INFO", ...},
  {"timestamp": "2026-03-07T10:30:01Z", "level": "INFO", ...}
]
```

**Pros**:
- Machine-parseable
- Structured data
- Schema can be enforced

**Cons**:
- **Can't append** (must rewrite entire file)
- Memory issues for large logs (must load entire file)
- Risk of corruption on crash (invalid JSON)

**Verdict**: ❌ **Rejected** - Append-only requirement for efficient logging

---

#### Option 3: JSONL (JSON Lines)
```jsonl
{"timestamp": "2026-03-07T10:30:00Z", "level": "INFO", "component": "filesystem_watcher", ...}
{"timestamp": "2026-03-07T10:30:01Z", "level": "INFO", "component": "filesystem_watcher", ...}
```

**Pros**:
- **Append-only** (efficient writes)
- Machine-parseable (line by line)
- Easy log rotation (close file, open new)
- Streaming-friendly (process as stream)
- Industry standard (used by Fluentd, Logstash, etc.)
- Schema can be enforced per line

**Cons**:
- Slightly larger file size than plain text (~10% overhead)

**Verdict**: ✅ **Selected** - Best balance of structure, efficiency, and operability

---

### 3. Path Handling

**Requirement**: FR-006 (path validation to prevent traversal)

#### Option 1: os.path (string-based)
```python
import os

def validate_path(file_path, vault_path):
    file_abs = os.path.abspath(file_path)
    vault_abs = os.path.abspath(vault_path)
    common = os.path.commonpath([file_abs, vault_abs])
    if common != vault_abs:
        raise ValueError("Path traversal attempt")
```

**Pros**:
- Built-in (no dependencies)
- Widely used
- Well-understood

**Cons**:
- Older API (Python 2 era)
- Less intuitive (string manipulation)
- Error-prone with edge cases (trailing slashes, etc.)
- No type safety

**Verdict**: ❌ **Rejected** - Older API, less secure

---

#### Option 2: pathlib (object-oriented)
```python
from pathlib import Path

def validate_path(file_path, vault_path):
    file_abs = Path(file_path).resolve()
    vault_abs = Path(vault_path).resolve()
    try:
        file_abs.relative_to(vault_abs)
    except ValueError:
        raise ValueError("Path traversal attempt")
```

**Pros**:
- **Modern API** (Python 3.4+)
- Intuitive (object-oriented)
- **Built-in security** (`resolve()` for absolute paths, `relative_to()` for containment)
- Better cross-platform handling
- Type hints support

**Cons**:
- Slightly more verbose for simple operations

**Verdict**: ✅ **Selected** - Modern, secure, intuitive API

---

### 4. Testing Framework

**Requirement**: Principle IX (80%+ coverage)

#### Option 1: unittest (built-in)
```python
import unittest

class TestFilesystemWatcher(unittest.TestCase):
    def test_dev_mode_validation(self):
        with self.assertRaises(SystemExit):
            FileSystemWatcher(vault_path, dev_mode=False)
```

**Pros**:
- Built into Python (no dependencies)
- Widely known
- Standard library

**Cons**:
- Verbose (boilerplate code)
- Limited fixtures
- No built-in coverage (needs coverage.py)
- No built-in mocking (needs unittest.mock)
- Less concise assertions

**Verdict**: ❌ **Rejected** - More code, less features

---

#### Option 2: pytest (industry standard)
```python
import pytest

def test_dev_mode_validation():
    with pytest.raises(SystemExit):
        FileSystemWatcher(vault_path, dev_mode=False)
```

**Pros**:
- **Concise syntax** (less boilerplate)
- **Built-in fixtures** (parametrize, fixtures, markers)
- **Coverage support** (pytest-cov plugin)
- **Mocking support** (pytest-mock plugin)
- Rich assertion introspection (shows variable values on failure)
- Industry standard (used by most Python projects)
- Rich plugin ecosystem

**Cons**:
- External dependency (but well-established)

**Verdict**: ✅ **Selected** - Industry standard, better features, less code

---

## Performance Benchmarks

### Expected Throughput

Based on watchdog documentation and real-world usage:

| Metric | Target | Expected |
|--------|--------|----------|
| File detection latency | <60 seconds | <1 second (event-driven) |
| Action file creation | <2 seconds (<10MB) | <0.5 seconds |
| Memory usage | <100MB | ~10-20MB |
| CPU usage | <5% | <1% (idle, event-driven) |
| Log write latency | <100ms | <10ms (append-only) |

### Scaling Considerations

| Files/day | Expected Load | Notes |
|-----------|---------------|-------|
| <100 | Light | No batching needed |
| 100-1000 | Moderate | May batch across cycles |
| 1000-10000 | Heavy | Consider interval tuning |
| >10000 | Very Heavy | Out of Bronze tier scope |

---

## Security Implications

### Path Traversal Attacks

**Attack Vector**: Malicious filename like `../../etc/passwd`

**Mitigation**:
1. Use `Path.resolve()` to get absolute path
2. Use `os.path.commonpath()` to verify containment
3. Reject any path outside vault_path
4. Log all traversal attempts at ERROR level

**Example**:
```python
def validate_path(file_path: str, vault_path: str) -> Path:
    file_abs = Path(file_path).resolve()
    vault_abs = Path(vault_path).resolve()
    try:
        # This raises ValueError if file_abs is not relative to vault_abs
        file_abs.relative_to(vault_abs)
        return file_abs
    except ValueError:
        logger.error(f"Path traversal attempt: {file_path}")
        raise ValueError(f"Path must be within vault: {vault_path}")
```

---

### File Permissions

**Risk**: Watcher running with elevated privileges could access files outside intended scope

**Mitigation**:
1. Run with minimal required permissions
2. Validate file readability before processing
3. Log permission errors (don't retry indefinitely)
4. Don't follow symlinks outside vault

---

### Log File Security

**Risk**: Audit logs could contain sensitive file names or metadata

**Mitigation**:
1. Log metadata only (not file contents)
2. Restrict log file permissions (chmod 600)
3. Rotate logs regularly (7 days)
4. Consider log encryption for sensitive deployments

---

## Best Practices

### 1. Error Handling

**Pattern**: Specific exception types with graceful recovery

```python
try:
    content = file_path.read_text()
except PermissionError as e:
    logger.error(f"Permission denied: {file_path}", exc_info=True)
    continue  # Skip this file, continue monitoring
except FileNotFoundError as e:
    logger.warning(f"File not found (may have been moved): {file_path}")
    retry_queue.append(file_path)
except OSError as e:
    if e.errno == 28:  # Disk full
        logger.critical("Disk full - halting watcher", exc_info=True)
        create_alert_file()
        break
    raise
```

---

### 2. Log Rotation

**Pattern**: Size and age-based rotation

```python
def rotate_logs(log_dir: Path, max_age_days: int = 7, max_size_mb: int = 100):
    for log_file in log_dir.glob("audit_*.jsonl"):
        # Check age
        age = datetime.now() - datetime.fromtimestamp(log_file.stat().st_mtime)
        if age.days > max_age_days:
            log_file.rename(log_file.with_suffix(".jsonl.archived"))
        
        # Check size
        if log_file.stat().st_size > max_size_mb * 1024 * 1024:
            log_file.rename(log_file.with_suffix(".jsonl.archived"))
    
    # Delete oldest archived logs (keep last 7)
    archived = sorted(log_dir.glob("*.archived"), key=lambda f: f.stat().st_mtime)
    for old_log in archived[:-7]:
        old_log.unlink()
```

---

### 3. Processed File Tracking

**Pattern**: In-memory hash set with path+modified_time

```python
class FileSystemWatcher(BaseWatcher):
    def __init__(self, vault_path: str, ...):
        self.processed_files: set[tuple[str, float]] = set()
    
    def is_processed(self, file_path: Path) -> bool:
        stat = file_path.stat()
        key = (str(file_path), stat.st_mtime)
        return key in self.processed_files
    
    def mark_processed(self, file_path: Path):
        stat = file_path.stat()
        key = (str(file_path), stat.st_mtime)
        self.processed_files.add(key)
```

**Note**: In-memory tracking is acceptable for Bronze tier. For Silver/Gold tiers, consider persistent tracking (SQLite database).

---

## References

- **watchdog documentation**: https://pypi.org/project/watchdog/
- **pathlib documentation**: https://docs.python.org/3/library/pathlib.html
- **pytest documentation**: https://docs.pytest.org/
- **JSONL specification**: http://jsonlines.org/
- **IEEE 1016 Standard**: https://standards.ieee.org/standard/1016-2020.html

---

**Version**: 1.0 | **Status**: Complete | **All NEEDS CLARIFICATION resolved**: ✅
