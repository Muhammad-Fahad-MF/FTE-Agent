---
id: 013
title: Implement BaseWatcher Contract Tests
stage: green
date_iso: 2026-03-17
surface: agent
model: qwen3-coder-plus
feature: 001-file-system-watcher
branch: main
user: Imperial_Legend
command: /sp.implement --task T020, T021, T022, and T023
labels: ["tests", "contract", "base-watcher", "tdd"]
links:
  spec: specs/001-file-system-watcher/spec.md
  plan: specs/001-file-system-watcher/plan.md
  tasks: specs/001-file-system-watcher/tasks.md
  adr: null
  pr: null
files_yaml:
  created:
    - FTE/tests/contract/test_base_watcher_contract.py
    - FTE/src/base_watcher.py
    - FTE/src/filesystem_watcher.py
    - FTE/src/__init__.py
    - FTE/tests/__init__.py
  modified:
    - specs/001-file-system-watcher/tasks.md
tests_yaml:
  - FTE/tests/contract/test_base_watcher_contract.py::TestBaseWatcherContract::test_watcher_interface
  - FTE/tests/contract/test_base_watcher_contract.py::TestBaseWatcherContract::test_watcher_initialization
  - FTE/tests/contract/test_base_watcher_contract.py::TestBaseWatcherContract::test_check_for_updates_signature
  - FTE/tests/contract/test_base_watcher_contract.py::TestBaseWatcherContract::test_create_action_file_signature
prompt_text: |
  /sp.implement --task T020, T021, T022, and T023
  
  Execute tasks T020-T023 which create contract tests for BaseWatcher interface:
  - T020: Create test_base_watcher_contract.py test file
  - T021: Implement test_watcher_interface() test
  - T022: Implement test_watcher_initialization() test
  - T023: Implement test_check_for_updates_signature() test
  
  Follow TDD approach: create tests first, then implement source code to make tests pass.
response_text: |
  Created contract tests and source files:
  - tests/contract/test_base_watcher_contract.py: 4 contract tests
  - src/base_watcher.py: Abstract base class
  - src/filesystem_watcher.py: Concrete implementation
  
  All 4 tests passing:
  ```
  tests/contract/test_base_watcher_contract.py::TestBaseWatcherContract::test_watcher_interface PASSED
  tests/contract/test_base_watcher_contract.py::TestBaseWatcherContract::test_watcher_initialization PASSED
  tests/contract/test_base_watcher_contract.py::TestBaseWatcherContract::test_check_for_updates_signature PASSED
  tests/contract/test_base_watcher_contract.py::TestBaseWatcherContract::test_create_action_file_signature PASSED
  
  4 passed in 0.13s
  ```
  
  Updated tasks.md to mark T020-T023 completed and compressed task details.
outcome: |
  T020-T023 completed successfully. Contract tests verify BaseWatcher interface:
  - Inheritance: FileSystemWatcher extends BaseWatcher
  - Constructor: __init__(vault_path, dry_run, interval)
  - Method: check_for_updates() -> list[Path]
  - Method: create_action_file() -> Path
evaluation: |
  All tests passing (4/4). Source code implements abstract base class pattern.
  Tasks marked complete in tasks.md with summary section.
---

# PHR: Implement BaseWatcher Contract Tests (T020-T023)

## Summary

Implemented contract tests for BaseWatcher interface following TDD approach.

## Files Created

**Tests**:
- `FTE/tests/contract/test_base_watcher_contract.py` - 4 contract tests

**Source**:
- `FTE/src/base_watcher.py` - Abstract base class
- `FTE/src/filesystem_watcher.py` - Concrete implementation
- `FTE/src/__init__.py`, `FTE/tests/__init__.py` - Package inits

## Test Results

```bash
cd FTE && pytest tests/contract/test_base_watcher_contract.py -v
# 4 passed in 0.13s
```

## Tasks Completed

- ✅ T020: Create test file
- ✅ T021: test_watcher_interface()
- ✅ T022: test_watcher_initialization()
- ✅ T023: test_check_for_updates_signature()

## Next Steps

Continue with T024+ (AuditLogger unit tests) or implement remaining contract test T024.
