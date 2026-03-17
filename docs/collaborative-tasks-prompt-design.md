# Collaborative Prompt Design Session: /sp.tasks for File System Watcher

**Participants**: Three Prompt Engineering Experts
**Goal**: Create the ultimate /sp.tasks prompt that extracts maximum performance from Qwen Code CLI
**Method**: Iterative critique and refinement (4 rounds)

---

## ROUND 1: Initial Proposals

### Expert A: Dr. Emily Carter (TDD & Testing Specialist)
**Focus**: Test-first approach, test ordering, coverage requirements, Red-Green-Refactor cycle

```text
You are a TDD Expert with 20+ years of experience in test-driven development, test ordering strategies, and coverage optimization.

PROJECT: FTE-Agent v3.0.0 - File System Watcher (Bronze P1)
SPEC: specs/001-file-system-watcher/spec.md
PLAN: specs/001-file-system-watcher/plan.md

YOUR TASK: Create a task breakdown that enforces strict test-first development with proper test ordering and coverage requirements.

CRITICAL REQUIREMENTS:
1. Tests MUST be written before implementation (Red-Green-Refactor)
2. Test ordering: Contract → Unit → Integration → Chaos
3. Each test task must specify exact test functions to implement
4. Coverage requirement: 80%+ (pytest-cov)
5. Quality gates: ruff, black, mypy, bandit (all 0 errors)

OUTPUT STRUCTURE:

# Tasks: File System Watcher (Bronze P1)

## Phase 0: Setup
- [ ] T001-T008: Project structure, tool configs, vault setup

## Phase 1: User Story 1 - Test-First Implementation

### Step 1: Contract Tests (RED)
- [ ] T009 [P] Create tests/contract/test_base_watcher_contract.py
  - test_watcher_interface() - verify inheritance
  - test_watcher_initialization() - verify __init__ signature
  - test_check_for_updates_signature() - verify return type
  - test_create_action_file_signature() - verify return type

### Step 2: Unit Tests (RED)
- [ ] T010 [P] Create tests/unit/test_audit_logger.py
  - test_log_entry_schema() - verify all 7 fields
  - test_log_rotation() - verify 7 days or 100MB
  - test_error_logging_with_stack_trace() - verify exc_info=True

- [ ] T011 [P] Create tests/unit/test_filesystem_watcher.py
  - test_dev_mode_validation() - verify exit code 1
  - test_path_validation_traversal_attempt() - verify ValueError
  - test_stop_file_detection() - verify halt within 60s
  - test_dry_run_no_file_creation() - verify no files created

### Step 3: Integration Tests (RED)
- [ ] T012 [P] Create tests/integration/test_watcher_to_action.py
  - test_file_detected_to_action_created() - end-to-end
  - test_action_file_metadata() - verify fields
  - test_stop_file_prevents_action_creation() - verify STOP

### Step 4: Implementation (GREEN)
- [ ] T013 [P] Create src/audit_logger.py (make T010 pass)
- [ ] T014 [P] Create src/base_watcher.py (make T009, T011 pass)
- [ ] T015 Create src/filesystem_watcher.py (make T012 pass)
- [ ] T016 Create src/skills.py (reusable functions)

### Step 5: Refactor
- [ ] Run all tests, verify 80%+ coverage
- [ ] Run quality gates (ruff, black, mypy, bandit)

**Checkpoint**: All tests GREEN, coverage verified

[Continue for US2, US3, Phase 4...]

QUALITY RULES:
✅ Tests BEFORE implementation (Red-Green-Refactor)
✅ Exact test function names specified
✅ Coverage 80%+ required
✅ Quality gates blocking merge
```

---

### Expert B: Marcus Johnson (Agile & Scrum Master)
**Focus**: User story organization, task sizing (4-16 hours), parallel execution, incremental delivery

```text
You are an Agile Coach with 20+ years of experience in sprint planning, task breakdown, and team velocity optimization.

PROJECT: FTE-Agent v3.0.0 - File System Watcher (Bronze P1)
SPEC: specs/001-file-system-watcher/spec.md
PLAN: specs/001-file-system-watcher/plan.md

YOUR TASK: Create a task breakdown optimized for agile delivery with proper task sizing, parallel execution, and incremental MVP releases.

CRITICAL REQUIREMENTS:
1. Each user story = separate phase (independently deliverable)
2. Task size: 4-16 hours each (completable in 1-2 days)
3. Mark parallel execution with [P]
4. MVP first approach (US1 only for quick win)
5. Checkpoint validations after each story

OUTPUT STRUCTURE:

# Tasks: File System Watcher (Bronze P1)

## Phase 0: Setup & Foundation (4-8 hours)
**Purpose**: Project initialization
**Dependencies**: None

- [ ] T001 Create project structure (src/, tests/, vault/)
- [ ] T002 Create pyproject.toml with dependencies
- [ ] T003 [P] Configure ruff
- [ ] T003 [P] Configure black
- [ ] T003 [P] Configure mypy
- [ ] T003 [P] Configure bandit
- [ ] T004 Create .gitignore
- [ ] T005 Create .env.example
- [ ] T006 Create vault/ directories
- [ ] T007 Create Dashboard.md
- [ ] T008 Create Company_Handbook.md

**Checkpoint**: `uv sync` succeeds, 0 errors

---

## Phase 1: User Story 1 - Detect and Process New Files (P1 - MVP) 🎯
**Goal**: File detection → action file creation
**Independent Test**: Drop file in Inbox/, verify action file in Needs_Action/
**Estimated**: 16-24 hours (4-6 tasks)

### Tests First
- [ ] T009 [P] Contract tests (tests/contract/)
- [ ] T010 [P] Unit tests - audit_logger (tests/unit/)
- [ ] T011 [P] Unit tests - filesystem_watcher (tests/unit/)
- [ ] T012 [P] Integration tests (tests/integration/)

### Implementation
- [ ] T013 [P] audit_logger.py (src/)
- [ ] T014 [P] base_watcher.py (src/)
- [ ] T015 filesystem_watcher.py (src/)
- [ ] T016 skills.py (src/)

**Checkpoint**: US1 tests pass, 80%+ coverage, MVP ready for demo

---

## Phase 2: User Story 2 - Handle Errors Gracefully (P1 - MVP)
**Goal**: Graceful error handling
**Estimated**: 12-16 hours

[Similar structure...]

---

## Phase 3: User Story 3 - Configure Watcher (P2)
**Goal**: Configuration via env vars and CLI
**Estimated**: 8-12 hours

[Similar structure...]

---

## Phase 4: Quality Gates & Validation (4-8 hours)
- [ ] T025 ruff check (0 errors)
- [ ] T026 black --check (passes)
- [ ] T027 mypy --strict (0 errors)
- [ ] T028 bandit -r (0 high-severity)
- [ ] T029 pytest --cov=src (80%+)
- [ ] T030 Create quickstart.md
- [ ] T031 Manual validation scenarios

---

## Dependencies & Execution Order

### Critical Path
```
Phase 0 → Phase 1 (US1) → Phase 2 (US2) → Phase 4
                      ↘ Phase 3 (US3) ↗
```

### Parallel Opportunities
- Phase 0: T003 configs run in parallel
- Phase 1: T009-T012 tests run in parallel
- Phase 1: T013-T014 core modules run in parallel

**Minimum Duration**: ~40-60 hours (5-8 days)

### MVP Strategy
1. Phase 0 + Phase 1 → MVP ready (file detection working)
2. Add Phase 2 → Error handling ready
3. Add Phase 3 → Configuration ready
4. Phase 4 → Production ready

QUALITY RULES:
✅ Task size 4-16 hours
✅ [P] for parallel execution
✅ Checkpoint after each story
✅ MVP first approach
```

---

### Expert C: Sarah Chen (Technical Architect)
**Focus**: Dependency ordering, exact file paths, implementation phases, architecture alignment

```text
You are a Principal Software Architect with 20+ years of experience in system design, dependency management, and implementation planning.

PROJECT: FTE-Agent v3.0.0 - File System Watcher (Bronze P1)
SPEC: specs/001-file-system-watcher/spec.md
PLAN: specs/001-file-system-watcher/plan.md

YOUR TASK: Create a task breakdown that respects architectural dependencies with exact file paths and proper implementation ordering.

CRITICAL REQUIREMENTS:
1. Dependency ordering: models → services → implementation
2. Exact file paths for every task (e.g., src/filesystem_watcher.py)
3. Architecture alignment (BaseWatcher → FileSystemWatcher → Skills)
4. IEEE 1016 Design Views traceability
5. Quality gates at each phase

OUTPUT STRUCTURE:

# Tasks: File System Watcher (Bronze P1)

## Phase 0: Foundation
**Purpose**: Project structure and tool configuration

- [ ] T001 Create directory structure:
  - src/ (source code)
  - tests/unit/, tests/integration/, tests/contract/, tests/chaos/
  - vault/Inbox/, vault/Needs_Action/, vault/Done/, vault/Logs/
- [ ] T002 Create pyproject.toml:
  - Dependencies: watchdog>=4.0.0, python-dotenv>=1.0.0
  - Dev dependencies: pytest, pytest-cov, pytest-mock
  - Tool configs: ruff, black, mypy, bandit, isort
- [ ] T003 Create .gitignore:
  - Exclude: .env, __pycache__/, Logs/, vault/, *.pid
- [ ] T004 Create .env.example:
  - DEV_MODE=true, DRY_RUN=true, VAULT_PATH=./vault
- [ ] T005 Create vault/ directories
- [ ] T006 Create Dashboard.md (placeholder)
- [ ] T007 Create Company_Handbook.md (placeholder)

**Checkpoint**: `uv sync` succeeds

---

## Phase 1: User Story 1 - Core Implementation

### Layer 1: Foundation (No dependencies)
- [ ] T008 [P] Create src/audit_logger.py
  - Class: AuditLogger
  - Methods: __init__, log, info, error, rotate_logs
  - File: src/audit_logger.py
  - Tests: tests/unit/test_audit_logger.py

- [ ] T009 [P] Create src/base_watcher.py
  - Class: BaseWatcher (ABC)
  - Methods: __init__, check_for_updates (abstract), create_action_file, run
  - File: src/base_watcher.py
  - Tests: tests/contract/test_base_watcher_contract.py

### Layer 2: Implementation (depends on Layer 1)
- [ ] T010 Create src/filesystem_watcher.py
  - Class: FileSystemWatcher(BaseWatcher)
  - Methods: check_for_updates, validate_path, check_stop_file
  - Depends on: T008 (AuditLogger), T009 (BaseWatcher)
  - File: src/filesystem_watcher.py
  - Tests: tests/unit/test_filesystem_watcher.py

- [ ] T011 Create src/skills.py
  - Functions: create_action_file, log_audit, check_dev_mode, validate_path
  - Depends on: T008 (AuditLogger)
  - File: src/skills.py
  - Tests: tests/unit/test_skills.py

### Layer 3: Integration (depends on Layer 2)
- [ ] T012 Create tests/integration/test_watcher_to_action.py
  - Tests: end-to-end file detection → action creation
  - Depends on: T010, T011
  - File: tests/integration/test_watcher_to_action.py

**Checkpoint**: All tests pass, 80%+ coverage

---

## Phase 2: User Story 2 - Error Handling

### Layer 1: Error Handling Extension
- [ ] T013 Add error handling to src/filesystem_watcher.py
  - try/except for PermissionError
  - try/except for FileNotFoundError
  - try/except for OSError errno 28 (DiskFullError)
  - File: src/filesystem_watcher.py
  - Tests: tests/unit/test_error_handling.py

- [ ] T014 Add create_alert_file() to src/skills.py
  - Format: ALERT_<error_type>_<timestamp>.md
  - File: src/skills.py
  - Tests: tests/unit/test_alert_file.py

### Layer 2: Recovery Logic
- [ ] T015 Add restart recovery to src/filesystem_watcher.py
  - Re-scan Inbox/ on startup
  - Filter by modification time (<24 hours)
  - File: src/filesystem_watcher.py
  - Tests: tests/chaos/test_watcher_failure_scenarios.py

**Checkpoint**: Chaos tests validate recovery

---

## Phase 3: User Story 3 - Configuration

- [ ] T016 Add env var support to src/filesystem_watcher.py
  - Read VAULT_PATH, DRY_RUN, WATCHER_INTERVAL
  - File: src/filesystem_watcher.py
  - Tests: tests/unit/test_configuration.py

- [ ] T017 Add CLI argument parsing to src/filesystem_watcher.py
  - Add --vault-path, --dry-run, --interval
  - File: src/filesystem_watcher.py
  - Tests: tests/unit/test_cli.py

**Checkpoint**: Configuration tests pass

---

## Phase 4: Quality Gates

- [ ] T018 Run ruff check src/ tests/ (0 errors)
- [ ] T019 Run black --check src/ tests/ (passes)
- [ ] T020 Run mypy --strict src/ tests/ (0 errors)
- [ ] T021 Run bandit -r src/ tests/ (0 high-severity)
- [ ] T022 Run pytest --cov=src (80%+ coverage)
- [ ] T023 Create quickstart.md
- [ ] T024 Manual validation scenarios

**Checkpoint**: All gates pass

---

## Dependency Graph

```
T001-T007 (Foundation)
    ↓
T008-T009 (Layer 1: Independent)
    ↓
T010-T011 (Layer 2: Depends on Layer 1)
    ↓
T012 (Layer 3: Integration)
```

QUALITY RULES:
✅ Exact file paths for every task
✅ Dependency ordering respected
✅ Layer-based implementation
✅ Architecture alignment
```

---

## ROUND 2: Cross-Review & Critique

### Expert A (Emily - TDD) reviews Expert B (Marcus - Agile):

**Strengths**:
- ✅ Excellent task sizing (4-16 hours) - realistic for estimation
- ✅ Clear parallel execution markers [P]
- ✅ MVP first approach enables quick wins
- ✅ Checkpoint validations after each story

**Weaknesses**:
- ❌ Test ordering not explicit enough (which tests first?)
- ❌ No specific test function names (hard to track coverage)
- ❌ Missing Red-Green-Refactor cycle enforcement
- ❌ File paths not specific enough (just directory level)

**Recommendation**: Keep task sizing and parallel markers, but add explicit test ordering and function names from my approach.

---

### Expert A (Emily - TDD) reviews Expert C (Sarah - Architect):

**Strengths**:
- ✅ Excellent dependency ordering (Layer 1 → Layer 2 → Layer 3)
- ✅ Exact file paths for every task
- ✅ Architecture alignment clear

**Weaknesses**:
- ❌ Tests mixed with implementation (not strictly test-first)
- ❌ No Red-Green-Refactor cycle visible
- ❌ Contract tests not prioritized first
- ❌ Layer structure may be over-engineering for Bronze tier

**Recommendation**: Keep file paths and dependency ordering, but restructure to enforce tests BEFORE implementation.

---

### Expert B (Marcus - Agile) reviews Expert A (Emily - TDD):

**Strengths**:
- ✅ Excellent test ordering (Contract → Unit → Integration → Chaos)
- ✅ Specific test function names (easy to track)
- ✅ Clear Red-Green-Refactor structure

**Weaknesses**:
- ❌ No task sizing (how long is T009-T016?)
- ❌ No parallel markers (which tests can run together?)
- ❌ No MVP strategy (can we deliver US1 only?)
- ❌ Too test-heavy (may slow down initial progress)

**Recommendation**: Keep test ordering and function names, but add task sizing and parallel markers.

---

### Expert B (Marcus - Agile) reviews Expert C (Sarah - Architect):

**Strengths**:
- ✅ Excellent file paths (exact files specified)
- ✅ Clear dependency graph
- ✅ Layer-based approach prevents circular dependencies

**Weaknesses**:
- ❌ No task sizing (T008-T012 could be 2 hours or 20 hours)
- ❌ No parallel markers (T008-T009 look parallel but not marked)
- ❌ Layer structure adds complexity for simple Bronze tier
- ❌ No MVP strategy

**Recommendation**: Keep file paths and dependency graph, but add task sizing and parallel markers.

---

### Expert C (Sarah - Architect) reviews Expert A (Emily - TDD):

**Strengths**:
- ✅ Excellent test-first enforcement
- ✅ Clear test categories (Contract, Unit, Integration, Chaos)
- ✅ Coverage requirement explicit (80%+)

**Weaknesses**:
- ❌ No file paths (where does test_watcher_interface() go?)
- ❌ No dependency ordering between tests
- ❌ No architecture alignment (which module first?)
- ❌ Test file structure not specified

**Recommendation**: Keep test-first and test categories, but add file paths and dependency ordering.

---

### Expert C (Sarah - Architect) reviews Expert B (Marcus - Agile):

**Strengths**:
- ✅ Excellent task sizing (4-16 hours)
- ✅ Clear parallel markers [P]
- ✅ MVP strategy enables incremental delivery

**Weaknesses**:
- ❌ File paths not specific enough (just "src/")
- ❌ No dependency ordering within phases
- ❌ No architecture alignment (BaseWatcher before FileSystemWatcher?)
- ❌ Test file structure not specified

**Recommendation**: Keep task sizing and parallel markers, but add exact file paths and dependency ordering.

---

## ROUND 3: Consensus & Synthesis

**Agreed Discards**:
- ❌ Layer-based structure (over-engineering for Bronze tier)
- ❌ Mixed test/implementation ordering (must be strictly test-first)
- ❌ Vague file paths (must be exact: src/filesystem_watcher.py)
- ❌ No task sizing (must be 4-16 hours)

**Agreed Keeps**:
- ✅ Test-first approach with Red-Green-Refactor (Emily)
- ✅ Test ordering: Contract → Unit → Integration → Chaos (Emily)
- ✅ Task sizing 4-16 hours (Marcus)
- ✅ Parallel markers [P] (Marcus)
- ✅ MVP first approach (Marcus)
- ✅ Exact file paths (Sarah)
- ✅ Dependency ordering (Sarah)
- ✅ Checkpoint validations (Marcus)

**Synthesis Approach**:
1. Use test-first structure from Emily (Red-Green-Refactor)
2. Add task sizing and parallel markers from Marcus
3. Add exact file paths and dependency ordering from Sarah
4. Combine all into unified prompt with clear phases

---

## ROUND 4: Final Refined Prompt

```text
You are an expert Technical Lead with 20+ years of experience in agile development, test-driven development (TDD), and task decomposition for AI-assisted implementation.

PROJECT: FTE-Agent v3.0.0 - Autonomous AI Employee
CONSTITUTION: .specify/memory/constitution.md (13 principles)
SPEC: specs/001-file-system-watcher/spec.md
PLAN: specs/001-file-system-watcher/plan.md
AI ENGINE: Qwen Code CLI (free OAuth tier - 1,000 calls/day, NO MCP support)
PATTERN: Python Skills (src/skills.py) replaces MCP servers
TIER: Bronze (file I/O only, no external APIs)

YOUR TASK: Create a comprehensive task breakdown that:
1. Enforces test-first approach (Red-Green-Refactor cycle)
2. Orders tests: Contract → Unit → Integration → Chaos
3. Respects dependencies (models → services → implementation)
4. Marks parallel execution with [P]
5. Sizes tasks 4-16 hours each (completable in 1-2 days)
6. Specifies exact file paths for every task
7. Enables MVP-first delivery (US1 only for quick win)
8. Includes checkpoint validations after each user story

CRITICAL CONSTRAINTS:
- Bronze tier scope ONLY (file I/O, no external APIs)
- Python Skills pattern (NO MCP servers)
- Test-first approach (tests BEFORE implementation)
- Quality gates blocking merge (ruff, black, mypy, bandit, pytest 80%+ coverage)

---

## REQUIRED OUTPUT STRUCTURE

# Tasks: File System Watcher (Bronze P1)

**Input**: Design documents from specs/001-file-system-watcher/
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅
**Tests**: Test-first approach (TDD) - tests written before implementation
**Organization**: Tasks grouped by user story for independent implementation and testing

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- **File paths**: Exact paths for every task (e.g., src/filesystem_watcher.py)
- **Task size**: 4-16 hours each (completable in 1-2 days)

---

## Phase 0: Setup & Foundation (Shared Infrastructure)

**Purpose**: Project initialization and basic structure
**Dependencies**: None - can start immediately
**Estimated Duration**: 4-8 hours (1-2 days)

### Tasks:
- [ ] T001 Create project directory structure (src/, tests/, vault/)
  - File: mkdir src/ tests/unit/ tests/integration/ tests/contract/ tests/chaos/ vault/Inbox/ vault/Needs_Action/ vault/Done/ vault/Logs/
  - Estimated: 1 hour

- [ ] T002 Create pyproject.toml with dependencies
  - File: pyproject.toml
  - Dependencies: watchdog>=4.0.0, python-dotenv>=1.0.0
  - Dev dependencies: pytest>=8.0.0, pytest-cov>=5.0.0, pytest-mock>=3.12.0
  - Estimated: 2 hours

- [ ] T003 [P] Configure ruff in pyproject.toml
  - File: pyproject.toml
  - Estimated: 1 hour

- [ ] T003 [P] Configure black in pyproject.toml
  - File: pyproject.toml
  - Estimated: 1 hour

- [ ] T003 [P] Configure mypy in pyproject.toml
  - File: pyproject.toml
  - Estimated: 1 hour

- [ ] T003 [P] Configure bandit in pyproject.toml
  - File: pyproject.toml
  - Estimated: 1 hour

- [ ] T003 [P] Configure isort in pyproject.toml
  - File: pyproject.toml
  - Estimated: 1 hour

- [ ] T004 Create .gitignore
  - File: .gitignore
  - Exclude: .env, __pycache__/, Logs/, vault/, *.pid
  - Estimated: 1 hour

- [ ] T005 Create .env.example template
  - File: .env.example
  - Content: DEV_MODE=true, DRY_RUN=true, VAULT_PATH=./vault
  - Estimated: 1 hour

- [ ] T006 Create vault/ directory structure
  - File: mkdir vault/Inbox/ vault/Needs_Action/ vault/Done/ vault/Logs/ vault/Pending_Approval/ vault/Approved/ vault/Rejected/
  - Estimated: 1 hour

- [ ] T007 Create Dashboard.md placeholder
  - File: vault/Dashboard.md
  - Estimated: 1 hour

- [ ] T008 Create Company_Handbook.md placeholder
  - File: vault/Company_Handbook.md
  - Estimated: 1 hour

**Checkpoint**: Foundation complete - run `uv sync` and verify 0 errors

---

## Phase 1: User Story 1 - Detect and Process New Files (Priority: P1 - MVP) 🎯

**Goal**: Implement file detection and action file creation
**Independent Test**: Drop file in Inbox/, verify action file created in Needs_Action/ within 60 seconds
**Estimated Duration**: 16-24 hours (4-6 days)

### Tests First (RED Phase) - Write BEFORE implementation

**Contract Tests** (verify interfaces):
- [ ] T009 [P] [US1] Create tests/contract/test_base_watcher_contract.py
  - File: tests/contract/test_base_watcher_contract.py
  - Functions: test_watcher_interface(), test_watcher_initialization(), test_check_for_updates_signature(), test_create_action_file_signature()
  - Estimated: 2 hours

**Unit Tests** (verify component behavior):
- [ ] T010 [P] [US1] Create tests/unit/test_audit_logger.py
  - File: tests/unit/test_audit_logger.py
  - Functions: test_log_entry_schema(), test_log_rotation(), test_error_logging_with_stack_trace()
  - Estimated: 3 hours

- [ ] T011 [P] [US1] Create tests/unit/test_filesystem_watcher.py
  - File: tests/unit/test_filesystem_watcher.py
  - Functions: test_dev_mode_validation(), test_path_validation_traversal_attempt(), test_stop_file_detection(), test_dry_run_no_file_creation()
  - Estimated: 4 hours

**Integration Tests** (verify component interaction):
- [ ] T012 [P] [US1] Create tests/integration/test_watcher_to_action.py
  - File: tests/integration/test_watcher_to_action.py
  - Functions: test_file_detected_to_action_created(), test_action_file_metadata(), test_stop_file_prevents_action_creation()
  - Estimated: 3 hours

### Implementation (GREEN Phase) - Make tests pass

**Core Implementation** (dependencies first):
- [ ] T013 [P] [US1] Create src/audit_logger.py
  - File: src/audit_logger.py
  - Class: AuditLogger
  - Methods: __init__(), log(), info(), error(), rotate_logs()
  - Depends on: None
  - Estimated: 4 hours

- [ ] T014 [P] [US1] Create src/base_watcher.py
  - File: src/base_watcher.py
  - Class: BaseWatcher (ABC)
  - Methods: __init__(), check_for_updates() (abstract), create_action_file(), run()
  - Depends on: T013 (AuditLogger)
  - Estimated: 4 hours

- [ ] T015 [US1] Create src/filesystem_watcher.py
  - File: src/filesystem_watcher.py
  - Class: FileSystemWatcher(BaseWatcher)
  - Methods: check_for_updates(), validate_path(), check_stop_file()
  - Depends on: T013 (AuditLogger), T014 (BaseWatcher)
  - Estimated: 6 hours

- [ ] T016 [US1] Create src/skills.py
  - File: src/skills.py
  - Functions: create_action_file(), log_audit(), check_dev_mode(), validate_path()
  - Depends on: T013 (AuditLogger)
  - Estimated: 4 hours

**Checkpoint**: All US1 tests pass (GREEN), 80%+ coverage verified, MVP ready for demo

---

## Phase 2: User Story 2 - Handle Errors Gracefully (Priority: P1 - MVP)

**Goal**: Implement graceful error handling for all exception types
**Independent Test**: Create error conditions, verify watcher logs error and continues
**Estimated Duration**: 12-16 hours (3-4 days)

### Tests First (RED Phase)

**Unit Tests**:
- [ ] T017 [P] [US2] Create tests/unit/test_error_handling.py
  - File: tests/unit/test_error_handling.py
  - Functions: test_permission_error_handling(), test_file_not_found_handling(), test_disk_full_handling(), test_unexpected_exception_handling()
  - Estimated: 3 hours

**Chaos Tests** (verify failure recovery):
- [ ] T018 [P] [US2] Create tests/chaos/test_watcher_failure_scenarios.py
  - File: tests/chaos/test_watcher_failure_scenarios.py
  - Functions: test_watcher_kill_mid_operation(), test_disk_full_graceful_halt(), test_corrupt_action_file_recovery(), test_watcher_restart_after_crash()
  - Estimated: 4 hours

### Implementation (GREEN Phase)

**Error Handling**:
- [ ] T019 [US2] Add error handling to src/filesystem_watcher.py
  - File: src/filesystem_watcher.py
  - Add: try/except for PermissionError, FileNotFoundError, OSError errno 28
  - Depends on: T015 (FileSystemWatcher)
  - Estimated: 4 hours

**Alert File Creation**:
- [ ] T020 [US2] Add create_alert_file() to src/skills.py
  - File: src/skills.py
  - Format: ALERT_<error_type>_<timestamp>.md
  - Depends on: T016 (Skills)
  - Estimated: 3 hours

**Recovery Logic**:
- [ ] T021 [US2] Add restart recovery to src/filesystem_watcher.py
  - File: src/filesystem_watcher.py
  - Add: re-scan Inbox/ on startup, filter by modification time (<24 hours)
  - Depends on: T019 (Error Handling)
  - Estimated: 4 hours

**Checkpoint**: All US2 tests pass (GREEN), chaos tests validate recovery

---

## Phase 3: User Story 3 - Configure Watcher Behavior (Priority: P2)

**Goal**: Implement configuration via environment variables and CLI flags
**Independent Test**: Set different configs, verify behavior changes
**Estimated Duration**: 8-12 hours (2-3 days)

### Tests First (RED Phase)

**Unit Tests**:
- [ ] T022 [P] [US3] Create tests/unit/test_configuration.py
  - File: tests/unit/test_configuration.py
  - Functions: test_vault_path_env_var(), test_interval_cli_flag(), test_dry_run_env_var(), test_cli_flag_precedence()
  - Estimated: 3 hours

### Implementation (GREEN Phase)

**Configuration**:
- [ ] T023 [P] [US3] Add environment variable support to src/filesystem_watcher.py
  - File: src/filesystem_watcher.py
  - Add: os.getenv() for VAULT_PATH, DRY_RUN, WATCHER_INTERVAL
  - Depends on: T015 (FileSystemWatcher)
  - Estimated: 3 hours

- [ ] T024 [US3] Add CLI argument parsing to src/filesystem_watcher.py
  - File: src/filesystem_watcher.py
  - Add: argparse for --vault-path, --dry-run, --interval
  - Depends on: T023 (Env Vars)
  - Estimated: 4 hours

**Checkpoint**: All US3 tests pass (GREEN), configuration verified

---

## Phase 4: Quality Gates & Validation

**Purpose**: Ensure all quality gates pass before implementation complete
**Dependencies**: All previous phases complete
**Estimated Duration**: 4-8 hours (1-2 days)

### Quality Gates:
- [ ] T025 Run ruff check src/ tests/ (0 errors required)
  - Command: ruff check src/ tests/
  - Estimated: 1 hour

- [ ] T026 Run black --check src/ tests/ (formatting passes)
  - Command: black --check src/ tests/
  - Estimated: 1 hour

- [ ] T027 Run mypy --strict src/ tests/ (0 errors required)
  - Command: mypy --strict src/ tests/
  - Estimated: 1 hour

- [ ] T028 Run bandit -r src/ tests/ (0 high-severity issues)
  - Command: bandit -r src/ tests/
  - Estimated: 1 hour

- [ ] T029 Run isort --check src/ tests/ (imports sorted)
  - Command: isort --check src/ tests/
  - Estimated: 1 hour

- [ ] T030 Run pytest --cov=src (80%+ coverage required)
  - Command: pytest --cov=src --cov-report=term-missing
  - Estimated: 2 hours

### Documentation:
- [ ] T031 Create specs/001-file-system-watcher/quickstart.md
  - File: specs/001-file-system-watcher/quickstart.md
  - Content: Prerequisites, validation scenarios, automated test commands, runbooks
  - Estimated: 3 hours

### Manual Validation:
- [ ] T032 Run quickstart.md validation scenarios
  - Scenarios: Happy path, edge case (10MB), error handling (PermissionError), security (path traversal), STOP file halt
  - Estimated: 2 hours

**Checkpoint**: All quality gates pass, manual validation complete

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 0 (Setup)**: No dependencies - start immediately
- **Phase 1 (US1)**: Depends on Phase 0 complete
- **Phase 2 (US2)**: Depends on Phase 1 complete
- **Phase 3 (US3)**: Depends on Phase 1 complete (can run parallel with Phase 2)
- **Phase 4 (Quality Gates)**: Depends on all phases complete

### Parallel Execution Opportunities
- **Phase 0**: T003 configs (ruff, black, mypy, bandit, isort) can run in parallel
- **Phase 1**: T009-T012 (tests) can run in parallel
- **Phase 1**: T013-T014 (core modules) can run in parallel
- **Phase 2**: T017-T018 (tests) can run in parallel
- **Phase 3**: T022 (tests) can run in parallel with T023 (env vars)

### Critical Path
```
Phase 0 → Phase 1 (US1) → Phase 2 (US2) → Phase 4 (Quality Gates)
                      ↘ Phase 3 (US3) ↗
```

**Minimum Duration**: ~40-60 hours (5-8 working days)

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 0: Setup
2. Complete Phase 1: User Story 1
3. **STOP and VALIDATE**: Test US1 independently
4. Deploy/demo if ready

### Incremental Delivery
1. Phase 0 + Phase 1 → MVP ready (file detection working)
2. Add Phase 2 → Error handling ready
3. Add Phase 3 → Configuration ready
4. Phase 4 → Production ready

### Parallel Team Strategy
With 2 developers:
- Developer A: Phase 1 (US1) - Core functionality
- Developer B: Phase 2 (US2) - Error handling (after Phase 1 foundation)
- Both: Phase 3 (US3) in parallel, Phase 4 together

---

## Notes

- **[P] tasks** = different files, no dependencies, can run in parallel
- **[Story] label** = maps task to user story for traceability
- **Test-first** = tests written and failing before implementation
- **Checkpoints** = validate independently before moving to next phase
- **File paths** = exact paths specified for every task
- **Task size** = 4-16 hours each (completable in 1-2 days)
- **Red-Green-Refactor** = tests first (RED), implementation (GREEN), refactor

---

## Quality Rules (STRICT ENFORCEMENT)

✅ USE: Exact file paths, test-first ordering, [P] for parallel tasks, 4-16 hour estimates
❌ NEVER: Vague tasks ("implement feature"), missing file paths, implementation before tests

## SELF-VALIDATION (BEFORE OUTPUT)

- [ ] All user stories from spec.md have corresponding task phases
- [ ] Tests ordered before implementation for each story (Red-Green-Refactor)
- [ ] Dependencies respected (models → services → implementation)
- [ ] Parallel opportunities marked with [P]
- [ ] Exact file paths specified for every task (e.g., src/filesystem_watcher.py)
- [ ] Checkpoint validations after each user story
- [ ] Quality gates included (ruff, black, mypy, bandit, pytest)
- [ ] Task size 4-16 hours each
- [ ] Bronze tier scope respected (no external APIs)
- [ ] Python Skills pattern used (no MCP)

Generate the complete task breakdown now.
```

---

## Final Consensus

**All Three Experts Agree**:

✅ **Test-First Structure**: Red-Green-Refactor cycle (Emily's contribution)  
✅ **Test Ordering**: Contract → Unit → Integration → Chaos (Emily's contribution)  
✅ **Task Sizing**: 4-16 hours each (Marcus's contribution)  
✅ **Parallel Markers**: [P] for parallel execution (Marcus's contribution)  
✅ **MVP Strategy**: US1 only for quick win (Marcus's contribution)  
✅ **Exact File Paths**: Every task has exact file path (Sarah's contribution)  
✅ **Dependency Ordering**: Models → Services → Implementation (Sarah's contribution)  
✅ **Checkpoint Validations**: After each user story (Marcus's contribution)  

**Key Improvements Over Individual Proposals**:
1. **Balanced rigor and practicality** (test-first + task sizing)
2. **Clear parallel execution** ([P] markers with dependency graph)
3. **Exact file paths** (no ambiguity about where code goes)
4. **MVP-first approach** (US1 only for quick win)
5. **Quality gates** (ruff, black, mypy, bandit, pytest 80%+)

---

**PHR Note**: This collaborative design session will be recorded in `history/prompts/tasks/016-collaborative-tasks-prompt-design.tasks.prompt.md`
