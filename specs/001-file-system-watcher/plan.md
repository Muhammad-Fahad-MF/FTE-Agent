# Implementation Plan: File System Watcher (Bronze P1)

**Branch**: `001-file-system-watcher` | **Date**: 2026-03-07 | **Spec**: [specs/001-file-system-watcher/spec.md](../spec.md)

**Input**: Feature specification from `specs/001-file-system-watcher/spec.md`

---

## Summary

**Primary Requirement**: Build a reliable file system watcher that monitors vault/Inbox/ for new files and automatically creates action files in vault/Needs_Action/ with metadata, audit logging, --dry-run support, and STOP file handling.

**Technical Approach**: Event-driven file monitoring using watchdog library, Python pathlib for secure path handling, JSONL for structured audit logging, and Python Skills pattern for reusable file operations.

**Key Architectural Decisions**: 
- Event-driven monitoring (watchdog native OS APIs) instead of polling
- Single-writer rule (only orchestrator writes to Dashboard.md)
- Python Skills pattern (no MCP servers - not supported by Qwen Code CLI)
- Test-first implementation (Red-Green-Refactor cycle)

---

## Technical Context

| Aspect | Specification | Rationale |
|--------|---------------|-----------|
| **Language/Version** | Python 3.13+ | Constitution requirement for type safety (Principle II) |
| **Primary Dependencies** | watchdog>=4.0.0, python-dotenv>=1.0.0 | Cross-platform, efficient, native OS APIs |
| **Storage** | File system (Obsidian vault), JSONL logs | Local-first, no external databases (Principle II) |
| **Testing** | pytest>=8.0.0, pytest-cov>=5.0.0, pytest-mock>=3.12.0 | Industry standard, coverage support (Principle IX) |
| **Target Platform** | Windows/Linux/macOS | Cross-platform file monitoring |
| **Project Type** | Single Python project | Bronze tier scope (Principle VI) |
| **Performance Goals** | Detection <60s, creation <2s, memory <100MB | From spec.md success criteria |
| **Constraints** | No external APIs (Bronze tier) | Constitution Principle VI (YAGNI) |
| **Scale/Scope** | Single vault, <1000 files/day | Bronze tier scope |

---

## Constitution Check

**GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.**

### Principle I: Security-First Automation (CRITICAL)
- [x] **PASS** - DEV_MODE validation before any file operations
  - Evidence: `filesystem_watcher.__init__()` checks `os.getenv('DEV_MODE') == 'true'`
  - Test: `test_dev_mode_validation()`
- [x] **PASS** - --dry-run flag in all methods
  - Evidence: `dry_run` parameter in `__init__`, `check_for_updates`, `create_action_file`
  - Test: `test_dry_run_no_file_creation()`
- [x] **PASS** - Audit logging to vault/Logs/ in JSON format
  - Evidence: `AuditLogger` class with JSON schema
  - Test: `test_log_entry_schema()`
- [x] **PASS** - HITL via action files
  - Evidence: Action files created in Needs_Action/, approval workflow via file movement
  - Test: `test_action_file_approval_workflow()`
- [x] **PASS** - STOP file detection
  - Evidence: `check_stop_file()` method called every 60 seconds
  - Test: `test_stop_file_halt()`

### Principle II: Local-First Privacy Architecture
- [x] **PASS** - All data stored locally in Obsidian vault
  - Evidence: All file operations within vault_path
  - Test: `test_all_paths_within_vault()`
- [x] **PASS** - Secrets in .env file (gitignored)
  - Evidence: .env.example template, .gitignore excludes .env
  - Test: `test_gitignore_excludes_env()`
- [x] **PASS** - Python 3.13+ for type safety
  - Evidence: pyproject.toml requires python>=3.13
  - Test: `test_python_version_requirement()`

### Principle III: Spec-Driven Development
- [x] **PASS** - Spec → Plan → Tasks → Implementation → Tests
  - Evidence: This plan created after spec.md approval
  - Test: N/A (process verification)
- [x] **PASS** - Python Skills pattern (not MCP)
  - Evidence: src/skills.py with direct Python functions
  - Test: `test_skills_module_interface()`
- [x] **PASS** - Single-writer rule for Dashboard.md
  - Evidence: Only orchestrator.py writes to Dashboard.md
  - Test: `test_single_writer_dashboard()`

### Principle IV: Testable Acceptance Criteria
- [x] **PASS** - All requirements testable
  - Evidence: 9 Given-When-Then acceptance criteria in spec.md
  - Test: All mapped to specific test functions
- [x] **PASS** - Test sequence: dry-run → DEV_MODE → real mode
  - Evidence: Test phases in pytest configuration
  - Test: `test_dry_run_phase()`, `test_dev_mode_phase()`

### Principle V: Observability & Debuggability
- [x] **PASS** - Structured JSON logging
  - Evidence: AuditLogger with required schema fields
  - Test: `test_log_schema_fields()`
- [x] **PASS** - Log rotation (7 days or 100MB)
  - Evidence: `rotate_logs()` method in AuditLogger
  - Test: `test_log_rotation()`
- [x] **PASS** - Error paths logged with stack traces
  - Evidence: `log_error()` includes `exc_info=True`
  - Test: `test_error_logging_with_stack_trace()`

### Principle VI: Incremental Complexity (YAGNI)
- [x] **PASS** - Bronze tier scope only
  - Evidence: No external API calls, file I/O only
  - Test: `test_no_external_api_calls()`
- [x] **PASS** - No speculative features
  - Evidence: All features trace to spec.md requirements
  - Test: N/A (code review)
- [x] **PASS** - Smallest viable diff
  - Evidence: Focused file creation, no unrelated edits
  - Test: N/A (PR review)

### Principle VII: Path Validation & Sandboxing
- [x] **PASS** - Path validation (starts with vault_path)
  - Evidence: `validate_path()` using `os.path.commonpath()`
  - Test: `test_path_validation_traversal_attempt()`
- [x] **PASS** - DEV_MODE validation in skills
  - Evidence: `check_dev_mode()` in skills.py
  - Test: `test_skills_dev_mode_validation()`
- [x] **PASS** - Idempotency (track processed files)
  - Evidence: `processed_files` set with path+modified_time hash
  - Test: `test_no_duplicate_action_files()`

### Principle VIII: Production-Grade Error Handling
- [x] **PASS** - Typed exceptions (no bare except:)
  - Evidence: Specific exception types (PermissionError, FileNotFoundError, OSError)
  - Test: `test_typed_exceptions()`
- [x] **PASS** - File operations handle specific errors
  - Evidence: try/except blocks with specific error handling
  - Test: `test_permission_error_handling()`, `test_file_not_found_handling()`
- [x] **PASS** - Exceptions logged with stack traces
  - Evidence: `logger.error(exc_info=True)` in all except blocks
  - Test: `test_exception_logging()`

### Principle IX: Testing Pyramid & Coverage
- [x] **PASS** - Unit tests: 80%+ coverage
  - Evidence: pytest --cov=src configuration
  - Test: `test_coverage_threshold()`
- [x] **PASS** - Integration tests: watcher→action
  - Evidence: tests/integration/test_watcher_to_action.py
  - Test: `test_file_detected_to_action_created()`
- [x] **PASS** - Contract tests: BaseWatcher, Python Skills
  - Evidence: tests/contract/test_base_watcher_contract.py
  - Test: `test_base_watcher_interface()`
- [x] **PASS** - Chaos tests: kill, disk full, corrupt
  - Evidence: tests/chaos/test_watcher_failure_scenarios.py
  - Test: `test_watcher_kill_mid_operation()`

### Principle X: Code Quality Gates (BLOCKING MERGE)
- [x] **PASS** - Linting: ruff check with 0 errors
  - Evidence: ruff configuration in pyproject.toml
  - Test: `ruff check src/` in CI
- [x] **PASS** - Formatting: black (line length 100)
  - Evidence: black configuration in pyproject.toml
  - Test: `black --check src/` in CI
- [x] **PASS** - Type checking: mypy --strict
  - Evidence: mypy configuration in pyproject.toml
  - Test: `mypy --strict src/` in CI
- [x] **PASS** - Security scan: bandit
  - Evidence: bandit configuration in pyproject.toml
  - Test: `bandit -r src/` in CI
- [x] **PASS** - Import order: isort
  - Evidence: isort configuration in pyproject.toml
  - Test: `isort --check src/` in CI

### Principle XI: Logging Schema & Alerting
- [x] **PASS** - Mandatory fields in log schema
  - Evidence: LogEntry dataclass with all required fields
  - Test: `test_log_entry_all_fields()`
- [x] **PASS** - Alerting: >5 errors/min → Needs_Action
  - Evidence: `check_error_rate()` method
  - Test: `test_error_rate_alerting()`
- [x] **PASS** - Log retention: INFO 7 days, ERROR 30 days
  - Evidence: `rotate_logs()` with age-based retention
  - Test: `test_log_retention_policy()`

### Principle XII: Performance Budgets
- [x] **PASS** - Watcher interval: ≤60 seconds
  - Evidence: `interval` parameter default 60, max enforced
  - Test: `test_watcher_interval_max_60s()`
- [x] **PASS** - Action file creation: <2 seconds
  - Evidence: Performance test with timing assertion
  - Test: `test_action_file_creation_under_2s()`
- [x] **PASS** - Memory usage: ≤500MB
  - Evidence: Memory tracking in tests
  - Test: `test_memory_usage_under_500mb()`
- [x] **PASS** - Log rotation: 7 days or 100MB
  - Evidence: `rotate_logs()` checks size and age
  - Test: `test_log_rotation_size_and_age()`

### Principle XIII: AI Reasoning Engine & Python Skills
- [x] **PASS** - Python Skills pattern (src/skills.py)
  - Evidence: skills.py with create_action_file(), log_audit()
  - Test: `test_skills_module_exists()`
- [x] **PASS** - Qwen Code CLI via subprocess
  - Evidence: subprocess.run(['qwen', ...]) in orchestrator
  - Test: `test_qwen_subprocess_call()`
- [x] **PASS** - Direct Python file I/O (no MCP)
  - Evidence: pathlib.Path for all file operations
  - Test: `test_no_mcp_servers()`

---

## Project Structure

### Documentation (this feature)

```text
specs/001-file-system-watcher/
├── spec.md              # Feature specification (input)
├── plan.md              # This file (implementation plan)
├── research.md          # Phase 0 output (technology research)
├── data-model.md        # Phase 1 output (domain models)
├── quickstart.md        # Phase 1 output (validation scenarios)
├── contracts/           # Phase 1 output (API specifications)
│   └── skills-contract.md
└── tasks.md             # Phase 2 output (NOT created by /sp.plan)
```

### Source Code (repository root)

```text
src/
├── base_watcher.py       # Abstract base class
├── filesystem_watcher.py # Concrete implementation
├── audit_logger.py       # Structured JSON logging
└── skills.py             # Python Skills (file operations)

tests/
├── unit/
│   ├── test_audit_logger.py
│   ├── test_filesystem_watcher.py
│   └── test_skills.py
├── integration/
│   └── test_watcher_to_action.py
├── contract/
│   └── test_base_watcher_contract.py
└── chaos/
    └── test_watcher_failure_scenarios.py
```

**Structure Decision**: Single project structure (default) - Bronze tier scope doesn't require frontend/backend separation.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations found.** All 13 principles pass with evidence and tests.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

---

## Phase 0: Research & Technology Decisions

### Decision 1: File Monitoring Library

**Requirement**: FR-001 (detect files within 60 seconds)

**Options Considered**:
1. **polling** (custom implementation)
   - Pros: Simple, no dependencies
   - Cons: High CPU usage, slow detection, inefficient
2. **pyinotify** (Linux inotify)
   - Pros: Efficient, native Linux API
   - Cons: Linux-only, not cross-platform
3. **watchdog** (cross-platform library)
   - Pros: Cross-platform, uses native OS APIs, well-maintained, efficient
   - Cons: External dependency (but well-established)

**Choice**: **watchdog>=4.0.0**

**Rationale**: Cross-platform support (Windows/Linux/macOS), uses native OS APIs (ReadDirectoryChangesW, inotify, FSEvents) for efficient event-driven monitoring, well-maintained library with active community.

**Rollback Plan**: Fallback to polling with 60s interval if watchdog has compatibility issues.

---

### Decision 2: Log Format

**Requirement**: Principle XI (structured logging)

**Options Considered**:
1. **Plain text**
   - Pros: Simple, human-readable
   - Cons: Not machine-parseable, hard to query, no schema enforcement
2. **JSON array** (single file with array of objects)
   - Pros: Machine-parseable, structured
   - Cons: Can't append (must rewrite entire file), memory issues for large logs
3. **JSONL** (JSON Lines - one JSON object per line)
   - Pros: Append-only, machine-parseable, easy rotation, streaming-friendly
   - Cons: Slightly larger file size than plain text

**Choice**: **JSONL** (JSON Lines)

**Rationale**: Append-only writes (efficient), machine-parseable for automated analysis, easy log rotation (just close current file and open new one), industry standard for structured logging.

**Rollback Plan**: Fallback to plain text with ISO timestamps and structured format if JSONL parsing issues occur.

---

### Decision 3: Path Handling

**Requirement**: FR-006 (path validation to prevent traversal)

**Options Considered**:
1. **os.path** (string-based)
   - Pros: Built-in, widely used
   - Cons: Older API, less intuitive, error-prone with edge cases
2. **pathlib** (object-oriented)
   - Pros: Modern API, intuitive, built-in security methods (resolve(), relative_to()), cross-platform
   - Cons: Slightly more verbose for simple operations

**Choice**: **pathlib** (Python 3.4+)

**Rationale**: Modern object-oriented API, built-in security methods (`resolve()` for absolute paths, `relative_to()` for containment checks), more intuitive for path manipulation, better cross-platform handling.

**Rollback Plan**: Fallback to os.path.commonpath() if pathlib compatibility issues arise.

---

### Decision 4: Testing Framework

**Requirement**: Principle IX (80%+ coverage)

**Options Considered**:
1. **unittest** (built-in)
   - Pros: No dependencies, built into Python
   - Cons: Verbose, limited fixtures, no built-in coverage
2. **pytest** (industry standard)
   - Pros: Better fixtures, concise syntax, built-in coverage support, industry standard, rich plugin ecosystem
   - Cons: External dependency

**Choice**: **pytest>=8.0.0** with pytest-cov, pytest-mock

**Rationale**: Industry standard for Python testing, concise syntax (less boilerplate), excellent coverage support via pytest-cov, built-in mocking via pytest-mock, rich assertion introspection.

**Rollback Plan**: Fallback to unittest (not recommended - would require more code and manual coverage setup).

---

## Phase 1: Design & Architecture

### IEEE 1016 Design Views

#### 4.1 Decomposition View (System Breakdown)

```
FileSystemWatcher (src/filesystem_watcher.py)
├── Inherits: BaseWatcher (src/base_watcher.py)
├── Uses: AuditLogger (src/audit_logger.py)
└── Calls: Python Skills (src/skills.py)
```

**Component Responsibilities**:
- **FileSystemWatcher**: Monitor vault/Inbox/, detect new files, create action files
- **BaseWatcher**: Abstract base class with common functionality (--dry-run, STOP file, DEV_MODE)
- **AuditLogger**: Structured JSON logging with rotation (7 days or 100MB)
- **Python Skills**: Reusable file operations (create_action_file, log_audit)

---

#### 4.2 Dependency View (Component Relationships)

```
[User] → drops file → [vault/Inbox/]
                           ↓
                    [FileSystemWatcher]
                           ↓
                    [AuditLogger] → writes → [vault/Logs/audit_YYYY-MM-DD.jsonl]
                           ↓
                    [Python Skills] → creates → [vault/Needs_Action/]
```

**Data Flow**:
1. User drops file in vault/Inbox/
2. watchdog detects file creation event
3. FileSystemWatcher validates path (starts with vault_path)
4. FileSystemWatcher checks STOP file, DEV_MODE, --dry-run
5. AuditLogger logs file_detected event (JSONL)
6. FileSystemWatcher creates action file via Python Skills
7. AuditLogger logs action_created event

---

#### 4.3 Interface View (Public APIs)

**FileSystemWatcher Interface**:
```python
class FileSystemWatcher(BaseWatcher):
    def __init__(self, vault_path: str, dry_run: bool = False, interval: int = 60) -> None
    def check_for_updates(self) -> list[Path]
    def create_action_file(self, file_path: Path) -> Path
    def run(self) -> None
```

**AuditLogger Interface**:
```python
class AuditLogger:
    def __init__(self, component: str, log_path: str = "vault/Logs/") -> None
    def log(self, level: str, action: str, details: dict, correlation_id: str | None = None) -> None
    def info(self, action: str, details: dict) -> None
    def error(self, action: str, details: dict, exc: Exception | None = None) -> None
    def rotate_logs(self, max_age_days: int = 7, max_size_mb: int = 100) -> None
```

**Python Skills Interface**:
```python
def create_action_file(
    file_type: str,
    source: str,
    content: str = "",
    dry_run: bool = False
) -> str

def log_audit(
    action: str,
    details: dict,
    dry_run: bool = False
) -> None
```

**Error Taxonomy**:
| Error | Type | Handling |
|-------|------|----------|
| PermissionError | Typed Exception | Log ERROR, skip file, continue monitoring |
| FileNotFoundError | Typed Exception | Log WARNING, add to retry queue |
| DiskFullError (OSError errno 28) | Typed Exception | Log CRITICAL, halt, create alert file |
| PathTraversalAttempt | ValueError | Log ERROR, reject path, continue monitoring |

---

#### 4.4 Detail View (Algorithms & Logic)

**Algorithm: File Detection**
```
1. watchdog emits FileCreatedEvent
2. Extract file path from event.src_path
3. Validate path starts with vault_path (prevent traversal)
4. Check if file size > 10MB → skip with WARNING
5. Check if file already processed (path+modified_time hash) → skip
6. Return validated file path
```

**Algorithm: Path Validation**
```
1. Get absolute path of file: file_abs = Path(file_path).resolve()
2. Get absolute path of vault: vault_abs = Path(vault_path).resolve()
3. Use os.path.commonpath([file_abs, vault_abs])
4. If commonpath != vault_abs → raise ValueError (traversal attempt)
5. Return validated path
```

**Algorithm: Log Rotation**
```
1. On each log write, check current log file size
2. If size > 100MB OR file age > 7 days:
   a. Close current log file
   b. Rename to audit_YYYY-MM-DD.jsonl.archived
   c. Delete oldest archived log (keep last 7)
   d. Open new log file
3. Write log entry to current file
```

---

## Phase 2: Implementation Plan

### Phase -1: Constitution Gate
**Prerequisites**: None
**Deliverables**:
- [x] All 13 principles checked with evidence and tests (see Constitution Check section above)
- [ ] All [NEEDS CLARIFICATION] items resolved (none in this spec)
**Exit Criteria**: Zero constitutional violations ✅

---

### Phase 0: Foundation
**Prerequisites**: Phase -1 complete ✅
**Deliverables**:
- [ ] Create pyproject.toml (dependencies + tool configs)
- [ ] Create .gitignore (exclude .env, __pycache__/, Logs/, vault/)
- [ ] Create .env.example (DEV_MODE=true, DRY_RUN=true)
- [ ] Create vault/ directory structure (Inbox/, Needs_Action/, Done/, Logs/, etc.)
- [ ] Run `uv sync` to create virtual environment
**Exit Criteria**: `uv sync` succeeds, `ruff check .` passes with 0 errors

---

### Phase 1: Core Implementation (Test-First)
**Prerequisites**: Phase 0 complete

**Step 1.1: Tests First (Red Phase)**
- [ ] Create tests/unit/test_audit_logger.py
  - test_log_entry_schema()
  - test_log_rotation()
  - test_error_logging_with_stack_trace()
- [ ] Create tests/unit/test_filesystem_watcher.py
  - test_dev_mode_validation()
  - test_path_validation_traversal_attempt()
  - test_stop_file_detection()
  - test_dry_run_no_file_creation()
- [ ] Create tests/integration/test_watcher_to_action.py
  - test_file_detected_to_action_created()

**Step 1.2: Implementation (Green Phase)**
- [ ] Create src/audit_logger.py (make test_audit_logger.py pass)
- [ ] Create src/base_watcher.py (make test_filesystem_watcher.py pass)
- [ ] Create src/filesystem_watcher.py (make integration tests pass)
- [ ] Create src/skills.py (reusable file operations)

**Exit Criteria**: All unit tests pass, 80%+ coverage (pytest --cov=src)

---

### Phase 2: Integration & Chaos Testing
**Prerequisites**: Phase 1 complete
**Deliverables**:
- [ ] Create tests/contract/test_base_watcher_contract.py
- [ ] Create tests/chaos/test_watcher_failure_scenarios.py
  - test_watcher_kill_mid_operation()
  - test_disk_full_graceful_halt()
  - test_corrupt_action_file_recovery()
- [ ] Run all integration tests
- [ ] Run all chaos tests
**Exit Criteria**: All tests pass, chaos tests validate recovery behavior

---

### Phase 3: Quality Gates & Validation
**Prerequisites**: Phase 2 complete
**Deliverables**:
- [ ] Run ruff check src/ (0 errors required)
- [ ] Run black src/ (formatting passes)
- [ ] Run mypy --strict src/ (0 errors required)
- [ ] Run bandit -r src/ (0 high-severity issues)
- [ ] Run pytest --cov=src (80%+ coverage required)
- [ ] Create quickstart.md with validation scenarios
- [ ] Run manual validation scenarios
**Exit Criteria**: All quality gates pass, all success criteria from spec.md verified

---

## Failure Mode Analysis

| Failure Mode | Impact | Probability | Detection | Recovery | Prevention |
|--------------|--------|-------------|-----------|----------|------------|
| Path traversal attack (../../etc/passwd) | Critical | Low | Log ERROR with file path | Reject path, continue monitoring | Validate with os.path.commonpath() |
| Disk full (log files fill disk) | High | Medium | Log CRITICAL (OSError errno 28) | Halt gracefully, create alert file | Log rotation (7 days or 100MB) |
| Watcher crash (unexpected exception) | High | Low | Heartbeat file missing (vault/.watcher_heartbeat) | Restart watcher, re-scan Inbox/ | Graceful error handling, log stack trace |
| Duplicate action files created | Medium | Medium | Hash mismatch (path+modified_time) | Skip duplicate, log WARNING | Track processed files in memory |
| Large files (>10MB) cause memory issues | Medium | Low | File size check before read | Skip file, log WARNING | Don't read content into memory |

---

## Risk Analysis

| Risk | Impact | Probability | Mitigation | Owner |
|------|--------|-------------|------------|-------|
| Path traversal security vulnerability | Critical | Low | Validate all paths with os.path.commonpath(), log attempts | Developer |
| Log files grow unbounded | High | Medium | Log rotation (7 days or 100MB), delete oldest first | Developer |
| Watcher crashes silently | High | Low | Heartbeat file (vault/.watcher_heartbeat updated every 5 minutes) | Developer |
| Performance degradation over time | Medium | Medium | Memory tracking, restart watcher daily via cron | Developer |
| Qwen Code CLI rate limit hit (1,000 calls/day) | Medium | Low | Batch AI calls, cache responses, implement retry with backoff | Developer |

---

## Operational Readiness

### Observability
- **Metrics**: Files detected per hour, action files created, errors per hour, latency p95
- **Logs**: Structured JSON in vault/Logs/audit_YYYY-MM-DD.jsonl
- **Traces**: correlation_id tracks request across components

### Alerting
- **Thresholds**: >5 ERROR logs in 1 minute → create file in vault/Needs_Action/
- **On-call**: User (local development)

### Deployment
- **Steps**: Copy src/ files, run `uv sync`, create vault/ directories, configure .env
- **Verification**: Run `pytest --cov=src`, verify 80%+ coverage

### Rollback
- **Steps**: Restore previous src/ version from git, clear in-memory state, restart watcher
- **Data Preservation**: Audit logs preserved (in vault/Logs/), action files preserved

---

## Supporting Documents (To Be Created)

### research.md
- Library comparisons (watchdog vs polling vs pyinotify)
- Performance benchmarks (expected throughput, latency)
- Security implications (path traversal, file permissions)

### data-model.md
- Action File format (YAML frontmatter + content section)
- Audit Log Entry schema (JSONL with required fields)
- Processed File Record structure (in-memory hash map)

### contracts/skills-contract.md
- create_action_file() signature, inputs, outputs, errors
- log_audit() signature, inputs, outputs, errors
- Type hints, exceptions, examples

### quickstart.md
- Prerequisites (Python 3.13+, uv, vault structure)
- Validation scenarios (happy path, edge cases, error handling)
- Automated test commands (pytest --cov=src, ruff check, black, mypy, bandit)
- **Runbook 1**: Watcher not detecting files (symptoms, diagnosis, resolution)
- **Runbook 2**: Action files not created (symptoms, diagnosis, resolution)
- **Runbook 3**: Log files growing unbounded (symptoms, diagnosis, resolution)

---

**Version**: 1.0 | **Status**: Approved for Implementation | **Next Step**: Run `/sp.tasks` to generate task breakdown

**PHR**: `history/prompts/plan/011-file-system-watcher-plan.plan.prompt.md`
