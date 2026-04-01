---
id: 47
title: Process Manager Implementation T031-T038
stage: green
date_iso: 2026-04-01
surface: agent
model: qwen-3-coder-plus
feature: 002-silver-tier-functional-assistant
branch: 002-silver-tier-functional-assistant
user: imperial_legend
command: /sp.implement --tasks T031-T038
labels: ["process-manager", "implementation", "silver-tier", "watchers", "health-monitoring"]
links:
  spec: specs/002-silver-tier-functional-assistant/spec.md
  plan: specs/002-silver-tier-functional-assistant/plan.md
  tasks: specs/002-silver-tier-functional-assistant/tasks.md
  adr: null
  pr: null
files_yaml:
  - src/process_manager.py
  - tests/unit/test_process_manager.py
  - tests/integration/test_process_manager_integration.py
  - tests/chaos/test_process_manager_chaos.py
  - src/audit_logger.py
  - specs/002-silver-tier-functional-assistant/tasks.md
tests_yaml:
  - tests/unit/test_process_manager.py (38 tests passing)
  - tests/integration/test_process_manager_integration.py
  - tests/chaos/test_process_manager_chaos.py
prompt_text: |
  /sp.implement --tasks T031-T038

  Execute the implementation plan by processing and executing all tasks defined in tasks.md for tasks T031-T038 (Process Manager implementation).

  Tasks to implement:
  - T031: Implement Process Manager class with start_all_watchers() and stop_all_watchers() methods
  - T032: Implement health monitoring checking watcher PIDs every 10 seconds
  - T033: Implement auto-restart for crashed watchers within 10 seconds
  - T034: Implement restart limits (max 3 restarts/hour per watcher)
  - T035: Implement memory monitoring using psutil (200MB threshold)
  - T036: Implement graceful shutdown handling SIGINT/SIGTERM
  - T037: Add metrics emission for process manager
  - T038: Write unit tests for process manager (38 tests)

  All tasks include integration tests and chaos tests as specified in tasks.md.
response_text: |
  Implemented Process Manager (src/process_manager.py) with:
  - start_all_watchers() and stop_all_watchers() methods using subprocess
  - Health monitoring every 10 seconds with process.poll()
  - Auto-restart within 10 seconds of crash detection
  - Restart limits (max 3/hour) with Dashboard.md alerts
  - Memory monitoring using psutil (200MB threshold)
  - Graceful shutdown via SIGINT/SIGTERM signal handlers
  - Metrics emission (process_manager_watcher_restarts, memory_usage, crash_count)

  Created comprehensive test suite:
  - 38 unit tests (100% passing)
  - Integration tests for crash/restart scenarios
  - Chaos tests for infinite crash loop prevention and graceful shutdown

  Quality gates:
  - ruff: All checks passed
  - black: Formatted
  - mypy --strict: Success (with --ignore-missing-imports for psutil)
  - pytest: 38/38 tests passing

  Also extended AuditLogger with warning() method for completeness.

  Updated tasks.md to mark T031-T038 as complete [X].
outcome: |
  ✅ All 8 tasks (T031-T038) implemented and tested
  ✅ 38 unit tests passing
  ✅ Integration tests created
  ✅ Chaos tests created
  ✅ All quality gates pass (ruff, black, mypy, pytest)
  ✅ tasks.md updated with completion status
evaluation: |
  Success criteria met:
  - ✅ Process Manager class with start/stop methods (T031)
  - ✅ Health monitoring every 10 seconds (T032)
  - ✅ Auto-restart within 10 seconds (T033)
  - ✅ Restart limits enforced (T034)
  - ✅ Memory monitoring with psutil (T035)
  - ✅ Graceful shutdown with signal handlers (T036)
  - ✅ Metrics emission (T037)
  - ✅ Unit tests with 85%+ coverage (T038) - 38 tests passing

  User Story 3 (Process Manager) is now independently functional.
  Next step: Continue with T039-T041 (FileSystem Watcher Extension).
