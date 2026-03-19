# Implementation Tasks: Silver Tier Functional Assistant

**Branch:** `002-silver-tier-functional-assistant`  
**Plan Version:** 2.0.0 (Production-Ready)  
**Spec Version:** 2.0.0  
**Total Tasks:** 115 (T001-T115)  
**Total Estimated Effort:** 70 hours  
**Timeline:** 4-5 weeks  

---

## Task Summary

| Phase | Tasks | Hours | Status |
|-------|-------|-------|--------|
| Phase 1: Foundation Extension | T001-T012 | 8h | ⏳ Pending |
| Phase 2: Perception Layer | T013-T041 | 18h | ⏳ Pending |
| Phase 3: Reasoning Layer | T042-T062 | 14h | ⏳ Pending |
| Phase 4: Action Layer | T063-T084 | 18h | ⏳ Pending |
| Phase 5: Production Readiness | T085-T115 | 12h | ⏳ Pending |

---

## Phase 1: Foundation Extension (8 hours)

**Purpose:** Extend Bronze tier foundation with production utilities (circuit breaker, metrics, logging, dead letter queue)

**Exit Criteria:**
- ✅ Vault structure extended (6 new folders + Failed_Actions/)
- ✅ Templates created (plan, approval, DLQ)
- ✅ Circuit breaker utility implemented with SQLite persistence
- ✅ Metrics collector implemented (Prometheus + SQLite)
- ✅ Log aggregator implemented with rotation
- ✅ All quality gates pass

---

### Phase 1 Tasks

#### Foundation Utilities (Production Critical)

- [ ] T001 [P] Extend vault structure: create Plans/, Pending_Approval/, Approved/, Rejected/, Briefings/, Templates/, Failed_Actions/ folders in FTE/vault/
  - **AC-1:** All 7 folders created under FTE/vault/
  - **AC-2:** Folder permissions allow read/write for current user
  - **AC-3:** .gitignore updated to exclude runtime files (*.db, *.log)
  - **AC-4:** Folder structure documented in README.md
  - **AC-5:** Manual verification: `dir FTE\vault\` shows all folders

- [ ] T002 [P] Create plan template in vault/Templates/plan_template.md with YAML frontmatter (created, status, objective, source_file, estimated_steps, requires_approval)
  - **AC-1:** File exists at vault/Templates/plan_template.md
  - **AC-2:** YAML frontmatter includes all 6 required fields
  - **AC-3:** Template includes step checkbox section
  - **AC-4:** Template includes notes section
  - **AC-5:** Template validated against spec.md Appendix A format

- [ ] T003 [P] Create approval request template in vault/Templates/approval_request_template.md with YAML frontmatter (type, action, action_details, created, expires, status, risk_level, reason)
  - **AC-1:** File exists at vault/Templates/approval_request_template.md
  - **AC-2:** YAML frontmatter includes all 8 required fields
  - **AC-3:** expires field set to created + 24 hours
  - **AC-4:** Template includes instructions for approve/reject
  - **AC-5:** Template validated against spec.md Section 6.6 format

- [ ] T004 [P] Create dead letter queue template in vault/Templates/dlq_template.md with YAML frontmatter (original_action, failure_reason, failure_count, last_attempt, details)
  - **AC-1:** File exists at vault/Templates/dlq_template.md
  - **AC-2:** YAML frontmatter includes all 5 required fields
  - **AC-3:** Template includes reprocessing instructions
  - **AC-4:** Template includes original action metadata section
  - **AC-5:** Template validated against plan.md ADR-009

- [ ] T005 Implement circuit breaker utility in src/utils/circuit_breaker.py with SQLite persistence (data/circuit_breakers.db), failure threshold=5, recovery timeout=60s, state change logging
  - **AC-1:** Circuit breaker trips after 5 consecutive failures (configurable threshold)
  - **AC-2:** Circuit breaker auto-resets after 60 seconds (configurable timeout)
  - **AC-3:** State persists to SQLite database (data/circuit_breakers.db)
  - **AC-4:** State survives application restart (read from DB on init)
  - **AC-5:** State changes logged with WARNING level (CLOSED→OPEN, OPEN→HALF_OPEN, HALF_OPEN→CLOSED)
  - **AC-6:** Manual reset method available (reset() function)
  - **AC-7:** Metrics emitted: circuit_breaker_state_change_count, circuit_breaker_rejection_count
  - **AC-8:** Supports decorator and context manager patterns
  - **AC-9:** Thread-safe implementation (supports concurrent calls)
  - **AC-10:** Includes fallback function support (optional fallback on failure)

- [ ] T006 Write unit tests for circuit breaker in tests/unit/test_circuit_breaker.py (test_trips_after_threshold, test_auto_resets, test_persists_state, test_recovers_on_restart, test_state_change_logging, test_manual_reset, test_decorator_pattern, test_context_manager, test_thread_safety, test_fallback_function)
  - **AC-1:** All 10 test functions implemented and passing
  - **AC-2:** Test coverage ≥90% for circuit_breaker.py
  - **AC-3:** Tests are independent (no test depends on another)
  - **AC-4:** Tests are repeatable (same result every run)
  - **AC-5:** All tests complete in <5 seconds total

- [ ] T007 Implement metrics collector in src/metrics/collector.py with Prometheus client + SQLite persistence, histogram/timer/counter/gauge support, metrics endpoint at /metrics
  - **AC-1:** Histogram metric type implemented with configurable buckets
  - **AC-2:** Counter metric type implemented with increment method
  - **AC-3:** Gauge metric type implemented with set/inc/dec methods
  - **AC-4:** Timer context manager implemented for duration tracking
  - **AC-5:** Metrics persist to SQLite (data/metrics.db)
  - **AC-6:** Prometheus format export via /metrics endpoint
  - **AC-7:** Metrics include: watcher_check_duration, action_file_creation_latency, approval_detection_latency
  - **AC-8:** Thread-safe metric updates
  - **AC-9:** SQLite connection pooling (max 5 connections)
  - **AC-10:** Metrics endpoint returns CONTENT_TYPE_LATEST format

- [ ] T008 Write unit tests for metrics collector in tests/unit/test_metrics_collector.py (test_histogram_recording, test_timer_context_manager, test_counter_increment, test_gauge_set, test_persistence, test_prometheus_format)
  - **AC-1:** All 6 test functions implemented and passing
  - **AC-2:** Test coverage ≥90% for collector.py
  - **AC-3:** Tests verify SQLite persistence
  - **AC-4:** Tests verify Prometheus format output
  - **AC-5:** Tests are independent and repeatable

- [ ] T009 Implement log aggregator in src/logging/log_aggregator.py with JSON logging, correlation_id support, daily rotation at 100MB, gzip compression for archived logs, retention (7 days INFO, 30 days ERROR/CRITICAL)
  - **AC-1:** All logs written in JSON format with required schema (timestamp, level, component, action, dry_run, correlation_id, details)
  - **AC-2:** correlation_id auto-generated per request/action if not provided
  - **AC-3:** Log rotation triggers at 100MB or daily (whichever first)
  - **AC-4:** Archived logs compressed with gzip (.gz extension)
  - **AC-5:** Retention policy enforced: 7 days INFO, 30 days ERROR/CRITICAL
  - **AC-6:** Logs written to vault/Logs/ directory
  - **AC-7:** Log file naming: app_YYYYMMDD_HHMMSS.log
  - **AC-8:** Concurrent write support (file locking)
  - **AC-9:** Async logging support (non-blocking writes)
  - **AC-10:** Log level configurable via Company_Handbook.md

- [ ] T010 Write unit tests for log aggregator in tests/unit/test_log_aggregator.py (test_json_format, test_correlation_id, test_rotation, test_compression, test_retention_policy, test_concurrent_writes)
  - **AC-1:** All 6 test functions implemented and passing
  - **AC-2:** Test coverage ≥90% for log_aggregator.py
  - **AC-3:** Tests verify JSON schema compliance
  - **AC-4:** Tests verify rotation at 100MB threshold
  - **AC-5:** Tests verify gzip compression of archived logs

- [ ] T011 Implement dead letter queue utility in src/utils/dead_letter_queue.py with SQLite storage (data/failed_actions.db), archive failed actions, retry tracking, manual reprocessing support
  - **AC-1:** Failed actions archived to SQLite (data/failed_actions.db)
  - **AC-2:** Archive includes: original_action, failure_reason, failure_count, last_attempt, details
  - **AC-3:** Retry count tracked per failed action
  - **AC-4:** Manual reprocess method available (reprocess(action_id))
  - **AC-5:** Query method for failed actions (get_failed_actions(limit=100))
  - **AC-6:** Failed actions also written to vault/Failed_Actions/ as .md files
  - **AC-7:** DLQ file format matches vault/Templates/dlq_template.md
  - **AC-8:** Thread-safe SQLite operations
  - **AC-9:** Metrics emitted: dlq_archive_count, dlq_reprocess_count
  - **AC-10:** Max retry limit enforced (default: 3, configurable)

- [ ] T012 Write unit tests for dead letter queue in tests/unit/test_dead_letter_queue.py (test_archive_action, test_retry_tracking, test_manual_reprocess, test_persistence, test_query_failed_actions)
  - **AC-1:** All 5 test functions implemented and passing
  - **AC-2:** Test coverage ≥90% for dead_letter_queue.py
  - **AC-3:** Tests verify SQLite persistence
  - **AC-4:** Tests verify file output to vault/Failed_Actions/
  - **AC-5:** Tests are independent and repeatable

**Phase 1 Checkpoint:** Foundation utilities complete with 90%+ test coverage

---

## Phase 2: Perception Layer (18 hours)

**Purpose:** Implement multi-source watchers (Gmail, WhatsApp, FileSystem) with circuit breakers, metrics, and Process Manager

**Exit Criteria:**
- ✅ Gmail Watcher operational (2-min interval, circuit breaker, metrics)
- ✅ WhatsApp Watcher operational (30-sec interval, keyword filtering, session preservation)
- ✅ Process Manager with health monitoring and auto-restart
- ✅ All watchers emit metrics and logs with correlation_id
- ✅ 85%+ test coverage

---

### User Story 1: Gmail Watcher (S1) - Priority P1 🎯

**Goal:** Monitor Gmail for unread/important emails every 2 minutes, create action files in Needs_Action/, track processed IDs

**Independent Test:** Gmail Watcher runs continuously, creates correctly formatted action files for new emails, skips already-processed messages

- [ ] T013 [P] [US1] Implement Gmail Watcher class in src/watchers/gmail_watcher.py extending BaseWatcher, interval=120s, check_for_updates() method querying Gmail API for unread/important messages
  - **AC-1:** Class extends BaseWatcher and implements all abstract methods
  - **AC-2:** check_for_updates() returns list of dicts with message metadata
  - **AC-3:** Only unread AND important messages returned (label:IMPORTANT)
  - **AC-4:** Check interval is 120 seconds (configurable)
  - **AC-5:** Gmail API called with correct query: `is:unread is:important`
  - **AC-6:** OAuth2 credentials loaded from environment variables
  - **AC-7:** Method returns empty list when no new messages
  - **AC-8:** Logs check execution with correlation_id

- [ ] T014 [US1] Implement create_action_file() method in src/watchers/gmail_watcher.py creating .md files in vault/Needs_Action/ with format: EMAIL_<message_id>.md, extracting From/To/Subject/Date/Snippet/Message-ID headers
  - **AC-1:** File created in vault/Needs_Action/ directory
  - **AC-2:** File naming: EMAIL_<message_id>.md (no spaces, URL-safe)
  - **AC-3:** YAML frontmatter includes: type, from, to, subject, received, priority, status, message_id
  - **AC-4:** Email headers extracted: From, To, Subject, Date, Snippet
  - **AC-5:** File content includes email snippet or full content
  - **AC-6:** Suggested actions section included with checkboxes
  - **AC-7:** File creation completes in <2 seconds (p95)
  - **AC-8:** File validated against spec.md Appendix A format

- [ ] T015 [US1] Implement processed ID tracking in src/watchers/gmail_watcher.py using SQLite (data/processed_emails.db), _track_processed(message_id), _is_processed(message_id) methods
  - **AC-1:** SQLite database created at data/processed_emails.db
  - **AC-2:** _track_processed() inserts message_id with timestamp
  - **AC-3:** _is_processed() returns True if message_id in database
  - **AC-4:** Processed IDs retained for 30 days (configurable)
  - **AC-5:** Old processed IDs auto-deleted after retention period
  - **AC-6:** Thread-safe SQLite operations
  - **AC-7:** Duplicate prevention verified (same message_id not processed twice)

- [ ] T016 [US1] Add circuit breaker to Gmail Watcher API calls in src/watchers/gmail_watcher.py using circuit_breaker utility, trips after 5 consecutive failures
  - **AC-1:** Circuit breaker wraps all Gmail API calls
  - **AC-2:** Circuit breaker trips after 5 consecutive failures
  - **AC-3:** Circuit breaker state persists to SQLite
  - **AC-4:** When OPEN, API calls fail fast without network request
  - **AC-5:** Circuit breaker auto-resets after 60 seconds
  - **AC-6:** State changes logged with WARNING level

- [ ] T017 [US1] Add metrics emission to Gmail Watcher in src/watchers/gmail_watcher.py: gmail_watcher_check_duration (histogram), gmail_watcher_items_processed (counter), gmail_watcher_errors (counter)
  - **AC-1:** gmail_watcher_check_duration histogram recorded per check
  - **AC-2:** gmail_watcher_items_processed counter incremented per new email
  - **AC-3:** gmail_watcher_errors counter incremented on error
  - **AC-4:** Metrics include correlation_id tag
  - **AC-5:** Metrics persisted to SQLite and exposed via /metrics

- [ ] T018 [US1] Implement session expiry detection in src/watchers/gmail_watcher.py detecting OAuth2 token expiry, logging WARNING, updating Dashboard.md, graceful halt
  - **AC-1:** OAuth2 token expiry detected (401 Unauthorized response)
  - **AC-2:** WARNING logged with message "Gmail OAuth2 token expired"
  - **AC-3:** Dashboard.md updated with expiry alert
  - **AC-4:** Watcher halts gracefully (no retry loop)
  - **AC-5:** User notification includes re-authentication instructions

- [ ] T019 [US1] Implement rate limiting in src/watchers/gmail_watcher.py (max 100 API calls/hour), configurable in Company_Handbook.md
  - **AC-1:** Rate limit enforced: max 100 calls/hour
  - **AC-2:** Configurable via Company_Handbook.md [Gmail] rate_limit_calls_per_hour
  - **AC-3:** Rate limit exceeded: log WARNING, skip check, retry next interval
  - **AC-4:** Rate limit counter persists across restarts
  - **AC-5:** Metrics emitted: gmail_watcher_rate_limit_hits

- [ ] T020 [US1] Write unit tests in tests/unit/test_gmail_watcher.py (test_check_returns_unread_important, test_filters_processed_ids, test_action_file_format, test_header_extraction, test_session_expiry, test_quota_exceeded_backoff, test_network_failure_retry, test_circuit_breaker_trips, test_metrics_emitted, test_rate_limiting)
  - **AC-1:** All 10 test functions implemented and passing
  - **AC-2:** Test coverage ≥85% for gmail_watcher.py
  - **AC-3:** External API calls mocked (no real Gmail calls)
  - **AC-4:** Tests are independent and repeatable
  - **AC-5:** All tests complete in <10 seconds total

- [ ] T021 [US1] Write integration tests in tests/integration/test_gmail_watcher_integration.py (test_creates_action_file_in_needs_action, test_action_file_triggers_plan_generation, test_processed_ids_persist_across_restarts)
  - **AC-1:** All 3 integration test functions implemented and passing
  - **AC-2:** Tests use real file system (temp directory)
  - **AC-3:** Tests verify end-to-end flow: watcher → action file → plan trigger
  - **AC-4:** Tests verify SQLite persistence across restarts
  - **AC-5:** Integration tests complete in <30 seconds

- [ ] T022 [US1] Write chaos tests in tests/chaos/test_gmail_watcher_chaos.py (test_recovers_from_api_failure, test_handles_session_expiry, test_restarts_after_crash_within_10s, test_continues_when_circuit_breaker_open)
  - **AC-1:** All 4 chaos test functions implemented and passing
  - **AC-2:** test_recovers_from_api_failure: simulates 503 errors, verifies recovery
  - **AC-3:** test_handles_session_expiry: mocks OAuth2 expiry, verifies graceful halt
  - **AC-4:** test_restarts_after_crash: kills process, verifies restart within 10s
  - **AC-5:** test_continues_when_circuit_breaker_open: verifies watcher continues other operations

**Checkpoint:** User Story 1 complete - Gmail Watcher independently functional

---

### User Story 2: WhatsApp Watcher (S2) - Priority P1

**Goal:** Monitor WhatsApp Web for keyword messages every 30 seconds, create action files, preserve session

**Independent Test:** WhatsApp Watcher detects messages with keywords (urgent, asap, invoice, payment, help), creates correctly formatted action files, survives restarts

- [ ] T023 [P] [US2] Implement WhatsApp Watcher class in src/watchers/whatsapp_watcher.py extending BaseWatcher, interval=30s, using Playwright for browser automation
  - **AC-1:** Class extends BaseWatcher and implements all abstract methods
  - **AC-2:** check_for_updates() returns list of dicts with keys: from, contact_name, message, received, keywords_matched
  - **AC-3:** Uses playwright.async_api with headless=True, user_data_dir=vault/whatsapp_session/
  - **AC-4:** Raises WhatsAppSessionExpired exception when session invalid
  - **AC-5:** Interval configurable via Company_Handbook.md [WhatsApp] check_interval_seconds

- [ ] T024 [US2] Implement check_for_updates() method in src/watchers/whatsapp_watcher.py scanning WhatsApp Web for new messages, returning list of message dicts
  - **AC-1:** Navigates to https://web.whatsapp.com and waits for message container selector
  - **AC-2:** Extracts last 10 messages from visible chat
  - **AC-3:** Handles StaleElementReferenceException with retry (max 3 attempts)
  - **AC-4:** Completes scan in <5 seconds (p95)

- [ ] T025 [US2] Implement keyword filtering in src/watchers/whatsapp_watcher.py with configurable keywords (urgent, asap, invoice, payment, help) from Company_Handbook.md
  - **AC-1:** _filter_by_keywords(messages: list[dict]) -> list[dict] method implemented
  - **AC-2:** Case-insensitive keyword matching
  - **AC-3:** keywords_matched list populated per message

- [ ] T026 [US2] Implement create_action_file() method in src/watchers/whatsapp_watcher.py creating WHATSAPP_<phone>_<timestamp>.md in vault/Needs_Action/ with From/Contact/Message/Received/Keywords metadata
  - **AC-1:** File naming: WHATSAPP_<phone_number>_<YYYYMMDD_HHMMSS>.md (phone sanitized: digits only)
  - **AC-2:** YAML frontmatter per spec.md Section 6.2 format
  - **AC-3:** File creation completes in <2 seconds (p95)

- [ ] T027 [US2] Implement session preservation in src/watchers/whatsapp_watcher.py saving session to vault/whatsapp_session/, recovering session on restart
  - **AC-1:** Session saved via context.storage_state(path=vault/whatsapp_session/storage.json)
  - **AC-2:** _recover_session() returns True if session valid, False if expired
  - **AC-3:** Dashboard.md updated with "WhatsApp session expired - please re-authenticate" on failure

- [ ] T028 [US2] Add circuit breaker to WhatsApp Watcher in src/watchers/whatsapp_watcher.py, trips after 5 consecutive Playwright failures
  - **AC-1:** Circuit breaker wraps check_for_updates() calls
  - **AC-2:** When OPEN: skips check and logs warning
  - **AC-3:** State persists to data/circuit_breakers.db

- [ ] T029 [US2] Add metrics emission to WhatsApp Watcher: whatsapp_watcher_check_duration, whatsapp_watcher_items_processed, whatsapp_watcher_errors
  - **AC-1:** Metrics include correlation_id tag
  - **AC-2:** Metrics persisted to SQLite and exposed via /metrics

- [ ] T030 [US2] Write unit tests in tests/unit/test_whatsapp_watcher.py
  - **AC-1:** test_keyword_filtering_returns_matching_messages
  - **AC-2:** test_session_preservation_saves_storage_state
  - **AC-3:** test_circuit_breaker_trips_after_5_failures
  - **AC-4:** All tests with Playwright calls mocked (no real browser)
  - **AC-5:** Test coverage ≥85% for whatsapp_watcher.py

- [ ] T030-INT Write integration tests in tests/integration/test_whatsapp_watcher_integration.py
  - **AC-1:** test_watcher_creates_action_file_in_needs_action
  - **AC-2:** test_session_persists_across_restarts
  - **AC-3:** Integration tests complete in <30 seconds

- [ ] T030-CHAOS Write chaos tests in tests/chaos/test_whatsapp_watcher_chaos.py
  - **AC-1:** test_browser_crash_recovery: verifies auto-restart within 10s
  - **AC-2:** test_session_expiry_handling: verifies graceful halt and Dashboard.md update
  - **AC-3:** test_continues_when_circuit_breaker_open

**Checkpoint:** User Story 2 complete - WhatsApp Watcher independently functional

---

### User Story 3: Process Manager (S3) - Priority P1

**Goal:** Keep all watchers running continuously with auto-recovery within 10 seconds

**Independent Test:** Process Manager starts all watchers, detects crashes, restarts within 10 seconds, enforces restart limits (max 3/hour)

- [ ] T031 [P] [US3] Implement Process Manager class in src/process_manager.py with start_all_watchers(), stop_all_watchers() methods using subprocess module
  - **AC-1:** start_all_watchers() launches gmail_watcher.py, whatsapp_watcher.py, filesystem_watcher.py as subprocesses
  - **AC-2:** stop_all_watchers() sends SIGTERM, waits 5 seconds, then SIGKILL
  - **AC-3:** Raises ProcessManagerError if watcher executable not found

- [ ] T032 [US3] Implement health monitoring in src/process_manager.py checking watcher PIDs every 10 seconds, detecting unexpected termination
  - **AC-1:** _check_watcher_health(name: str) -> bool uses process.poll()
  - **AC-2:** Health check interval: 10 seconds (configurable)
  - **AC-3:** Termination detected within 15 seconds of crash (p95)

- [ ] T033 [US3] Implement auto-restart in src/process_manager.py restarting crashed watchers within 10 seconds, logging restart events
  - **AC-1:** Restart triggered within 10 seconds of crash detection (p95)
  - **AC-2:** Restart count tracked per watcher in _restart_counts dict
  - **AC-3:** Metrics emitted: process_manager_watcher_restarts counter

- [ ] T034 [US3] Implement restart limits in src/process_manager.py (max 3 restarts/hour per watcher), preventing infinite crash loops
  - **AC-1:** Max 3 restarts per hour enforced per watcher
  - **AC-2:** When limit exceeded: CRITICAL log and Dashboard.md alert
  - **AC-3:** Restart count resets after 1 hour of no restarts

- [ ] T035 [US3] Implement memory monitoring in src/process_manager.py using psutil, killing watchers exceeding 200MB, logging alerts
  - **AC-1:** Uses psutil.Process(pid).memory_info().rss / 1024 / 1024
  - **AC-2:** Memory threshold: 200MB (configurable via Company_Handbook.md)
  - **AC-3:** When exceeded: WARNING log, kill watcher, restart if under limit

- [ ] T036 [US3] Implement graceful shutdown in src/process_manager.py handling SIGINT/SIGTERM, stopping all watchers cleanly
  - **AC-1:** signal.signal registered for SIGINT and SIGTERM
  - **AC-2:** Shutdown completes within 10 seconds (p95)
  - **AC-3:** Exit code 0 on graceful shutdown

- [ ] T037 [US3] Add metrics emission: process_manager_watcher_restarts, process_manager_memory_usage, process_manager_crash_count
  - **AC-1:** Metrics include watcher_name tag
  - **AC-2:** Metrics persisted to SQLite and exposed via /metrics

- [ ] T038 [US3] Write unit tests in tests/unit/test_process_manager.py
  - **AC-1:** test_crash_detection_via_poll
  - **AC-2:** test_restart_within_10_seconds
  - **AC-3:** test_restart_limits_enforced
  - **AC-4:** test_memory_monitoring_with_psutil
  - **AC-5:** All subprocess calls mocked (no real processes)
  - **AC-6:** Test coverage ≥85% for process_manager.py

- [ ] T038-INT Write integration tests in tests/integration/test_process_manager_integration.py
  - **AC-1:** test_watcher_crash_triggers_restart
  - **AC-2:** test_memory_limit_kills_watcher
  - **AC-3:** Integration tests complete in <60 seconds

- [ ] T038-CHAOS Write chaos tests in tests/chaos/test_process_manager_chaos.py
  - **AC-1:** test_infinite_crash_loop_prevented
  - **AC-2:** test_graceful_shutdown_under_load

**Checkpoint:** User Story 3 complete - Process Manager independently functional

---

### Phase 2: FileSystem Watcher Extension (Bronze → Silver)

- [ ] T039 [P] Extend FileSystem Watcher in src/filesystem_watcher.py to emit metrics (filesystem_watcher_check_duration, filesystem_watcher_items_processed)
  - **AC-1:** filesystem_watcher_check_duration histogram recorded per check
  - **AC-2:** filesystem_watcher_items_processed counter incremented per new file detected
  - **AC-3:** filesystem_watcher_errors counter incremented on exception
  - **AC-4:** Metrics include source_folder, file_extension tags
  - **AC-5:** Metrics persisted to SQLite and exposed via /metrics endpoint
  - **AC-6:** Existing Bronze tier functionality preserved (no breaking changes)

- [ ] T040 Extend FileSystem Watcher to add circuit breaker for file operations
  - **AC-1:** Circuit breaker wraps check_for_updates() method
  - **AC-2:** Uses circuit_breaker utility from src/utils/circuit_breaker.py
  - **AC-3:** failure_threshold=5, recovery_timeout=60 (configurable)
  - **AC-4:** When OPEN: logs "Circuit breaker OPEN - skipping FileSystem check"
  - **AC-5:** State persists to data/circuit_breakers.db
  - **AC-6:** State changes logged with WARNING level
  - **AC-7:** Circuit breaker only wraps file system operations (not timer)

- [ ] T041 Write tests for extended FileSystem Watcher in tests/unit/test_filesystem_watcher.py
  - **AC-1:** test_metrics_emitted_on_check: verifies histogram and counter recorded
  - **AC-2:** test_circuit_breaker_trips_after_failures: mocks file system errors, verifies breaker opens
  - **AC-3:** test_filesystem_watcher_preserves_bronze_functionality: verifies existing tests still pass
  - **AC-4:** test_new_file_detected_and_action_created: verifies end-to-end flow
  - **AC-5:** All 4 test functions implemented and passing
  - **AC-6:** Test coverage ≥85% for filesystem_watcher.py extensions
  - **AC-7:** Existing Bronze tier tests unchanged

**Phase 2 Checkpoint:** Perception Layer complete - All watchers running with Process Manager

---

## Phase 3: Reasoning Layer (14 hours)

**Purpose:** Implement Python Skills for plan generation, approval requests, and briefing generation

**Exit Criteria:**
- ✅ create_plan skill generates structured plans with YAML frontmatter
- ✅ request_approval skill creates approval files with 24-hour expiry
- ✅ generate_briefing skill creates daily/weekly briefings
- ✅ All skills validate DEV_MODE, support --dry-run, emit metrics
- ✅ 85%+ test coverage

---

### User Story 4: Plan Generation (S4) - Priority P1

**Goal:** Create structured Plan.md files from action files with YAML frontmatter and step checkboxes

**Independent Test:** New file in Needs_Action/ triggers plan generation, Plan.md created with correct format, status tracking works

- [ ] T042 [P] [US4] Implement create_plan skill in src/skills/create_plan.py with generate_plan(action_file: Path) -> Path method
  - **AC-1:** generate_plan(action_file: Path) -> Path method implemented
  - **AC-2:** Extends BaseSkill class from src/skills/base_skill.py
  - **AC-3:** Reads action file YAML frontmatter using yaml.safe_load()
  - **AC-4:** Extracts objective from action file content (first non-empty line after frontmatter)
  - **AC-5:** Returns Path to created plan file
  - **AC-6:** DEV_MODE validated (no external calls, safe to run)
  - **AC-7:** Correlation ID included in all logs
  - **AC-8:** Raises PlanGenerationError on invalid action file format

- [ ] T043 [US4] Implement YAML frontmatter generation in src/skills/create_plan.py (created, status, objective, source_file, estimated_steps, requires_approval)
  - **AC-1:** YAML frontmatter includes: created (ISO timestamp), status (pending), objective (string), source_file (Path), estimated_steps (int), requires_approval (bool)
  - **AC-2:** created field set to datetime.now().isoformat()
  - **AC-3:** status field initialized to "pending"
  - **AC-4:** objective extracted from action file content (truncated to 100 chars)
  - **AC-5:** source_file is absolute path to original action file
  - **AC-6:** estimated_steps calculated from content analysis (default: 5)
  - **AC-7:** requires_approval set based on action type (email/linkedin = True, file = False)
  - **AC-8:** Frontmatter validated against plan_template.md schema

- [ ] T044 [US4] Implement step extraction in src/skills/create_plan.py parsing action file content, generating step checkboxes
  - **AC-1:** _extract_steps(content: str) -> list[str] method implemented
  - **AC-2:** Steps extracted from "Suggested Actions" section of action file
  - **AC-3:** Each step formatted as: "- [ ] **Step {n}:** {action} (pending)"
  - **AC-4:** Minimum 3 steps generated (split complex actions if needed)
  - **AC-5:** Maximum 10 steps (consolidate if more)
  - **AC-6:** Steps include estimated duration comment (e.g., "# ~10 min")
  - **AC-7:** Steps section includes "## Steps" header
  - **AC-8:** Notes section included at end: "## Notes\n\n[Additional context]"

- [ ] T045 [US4] Implement status tracking in src/skills/create_plan.py with update_plan_status(plan_file, new_status), mark_step_complete(plan_file, step_number), get_plan_status(plan_file) methods
  - **AC-1:** update_plan_status(plan_file: Path, new_status: str) -> None method implemented
  - **AC-2:** Valid statuses: pending, in_progress, awaiting_approval, completed, cancelled
  - **AC-3:** Invalid status raises ValueError: "Invalid status: {status}"
  - **AC-4:** mark_step_complete(plan_file: Path, step_number: int) -> None marks checkbox as [x]
  - **AC-5:** get_plan_status(plan_file: Path) -> str returns current status from frontmatter
  - **AC-6:** File locking implemented to prevent concurrent update race conditions
  - **AC-7:** Status changes logged with INFO level
  - **AC-8:** Metrics emitted: plan_status_changes counter

- [ ] T046 [US4] Add file locking to src/skills/create_plan.py preventing concurrent update race conditions
  - **AC-1:** Uses portalocker or fcntl for cross-platform file locking
  - **AC-2:** _acquire_lock(plan_file: Path) -> Lock method implemented
  - **AC-3:** _release_lock(lock: Lock) method implemented
  - **AC-4:** Lock timeout: 10 seconds (raises LockTimeout exception)
  - **AC-5:** All plan file writes wrapped with lock acquisition
  - **AC-6:** Lock failures logged with WARNING level
  - **AC-7:** Metrics emitted: plan_lock_acquisitions, plan_lock_timeouts

- [ ] T047 [US4] Add circuit breaker and metrics to create_plan skill
  - **AC-1:** Circuit breaker wraps generate_plan() method (protects against file system failures)
  - **AC-2:** Uses circuit_breaker utility from src/utils/circuit_breaker.py
  - **AC-3:** failure_threshold=5, recovery_timeout=60
  - **AC-4:** create_plan_duration histogram recorded per plan generation
  - **AC-5:** create_plan_count counter incremented on success
  - **AC-6:** create_plan_errors counter incremented on exception
  - **AC-7:** Metrics include action_type tag (email, whatsapp, file)

- [ ] T048 [US4] Write unit tests in tests/unit/test_create_plan.py
  - **AC-1:** test_plan_generation_from_action_file: verifies plan.md created with correct format
  - **AC-2:** test_yaml_frontmatter_includes_all_fields: verifies 6 required fields present
  - **AC-3:** test_step_extraction_from_suggested_actions: verifies steps parsed correctly
  - **AC-4:** test_status_updates_modify_frontmatter: verifies YAML updated correctly
  - **AC-5:** test_concurrent_updates_use_file_locking: verifies no race conditions
  - **AC-6:** test_invalid_action_file_raises_error: verifies PlanGenerationError raised
  - **AC-7:** All 6 test functions implemented and passing
  - **AC-8:** Test coverage ≥85% for create_plan.py

- [ ] T048-INT Write integration tests in tests/integration/test_create_plan_integration.py
  - **AC-1:** test_action_file_triggers_plan_generation: drops file in Needs_Action/, verifies Plan.md created
  - **AC-2:** test_plan_status_tracking_across_updates: verifies status transitions work
  - **AC-3:** All 2 integration tests implemented and passing
  - **AC-4:** Integration tests complete in <30 seconds

**Checkpoint:** User Story 4 complete - Plan Generation independently functional

---

### User Story 5: HITL Approval Workflow (S6) - Priority P1

**Goal:** Require human approval for sensitive actions with 24-hour expiry

**Independent Test:** Approval request created for sensitive actions, file move to Approved/ detected within 5 seconds, expired approvals flagged

- [ ] T049 [P] [US5] Implement request_approval skill in src/skills/request_approval.py with create_approval_request(action: dict, reason: str) -> Path method
- [ ] T050 [US5] Implement approval file format in src/skills/request_approval.py with YAML frontmatter (type, action, action_details, created, expires, status, risk_level, reason)
- [ ] T051 [US5] Implement expiry handling in src/skills/request_approval.py with check_expiry() -> list[Path], flag_expired(expired_files) updating Dashboard.md
- [ ] T052 [US5] Implement approval handler in src/approval_handler.py with monitor_approved_folder() detecting file moves within 5 seconds (p95)
- [ ] T053 [US5] Implement rejection handling in src/approval_handler.py detecting moves to Rejected/, logging cancellations
- [ ] T054 [US5] Add circuit breaker and metrics to approval workflow
- [ ] T055 [US5] Write unit + integration + chaos tests in tests/unit/test_approval_handler.py, tests/integration/, tests/chaos/ (test_approval_file_creation, test_expiry_detection, test_file_move_detection, test_rejection_handling, test_concurrent_moves)

**Checkpoint:** User Story 5 complete - HITL Approval Workflow independently functional

---

### User Story 6: Briefing Generation (S8 partial) - Priority P2

**Goal:** Generate daily briefings and weekly audits from vault data

**Independent Test:** Daily briefing generated at 8 AM with pending/in-progress/completed summary, weekly audit generated Sunday 10 PM with metrics

- [ ] T056 [P] [US6] Implement generate_briefing skill in src/skills/generate_briefing.py with generate_daily_briefing(date) -> Path, generate_weekly_audit(date) -> Path methods
- [ ] T057 [US6] Implement daily briefing content in src/skills/generate_briefing.py summarizing Needs_Action/, Plans/, Done/ folders
- [ ] T058 [US6] Implement weekly audit content in src/skills/generate_briefing.py with metrics, watcher uptime, approval stats, bottlenecks, recommendations
- [ ] T059 [US6] Add metrics emission to briefing generation
- [ ] T060 [US6] Write unit + integration tests in tests/unit/test_generate_briefing.py, tests/integration/ (test_daily_briefing_format, test_weekly_audit_metrics, test_content_generation)

**Checkpoint:** User Story 6 complete - Briefing Generation independently functional

---

### Phase 3: Skill Infrastructure

- [ ] T061 [P] Implement skill base class in src/skills/base_skill.py with DEV_MODE validation, --dry-run support, correlation_id logging, metrics emission
- [ ] T062 Write tests for base skill in tests/unit/test_base_skill.py

**Phase 3 Checkpoint:** Reasoning Layer complete - All skills functional

---

## Phase 4: Action Layer (18 hours)

**Purpose:** Implement action skills (Email, LinkedIn) with approval integration, circuit breakers, rate limiting

**Exit Criteria:**
- ✅ send_email skill sends/drafts emails via Gmail API with --dry-run
- ✅ linkedin_posting skill posts to LinkedIn via Playwright with session recovery
- ✅ Approval handler integrated with dead letter queue
- ✅ All action skills implement circuit breakers, rate limiting, graceful degradation
- ✅ 85%+ test coverage

---

### User Story 7: Email Action Skill (S5) - Priority P1

**Goal:** Send/draft emails via Gmail API with approval for new contacts, --dry-run mode

**Independent Test:** Email skill sends test email, --dry-run logs without sending, new contacts trigger approval

- [ ] T063 [P] [US7] Implement send_email skill in src/skills/send_email.py with send_email(to, subject, body, attachments) -> dict, draft_email(to, subject, body) -> dict methods
  - **AC-1:** send_email() and draft_email() methods with signatures per spec.md Section 6.5
  - **AC-2:** Return dict includes: message_id, status, timestamp, dry_run
  - **AC-3:** Extends BaseSkill, validates DEV_MODE, supports --dry-run
  - **AC-4:** Raises ApprovalRequired exception when approval needed

- [ ] T064 [US7] Implement Gmail API integration in src/skills/send_email.py using google-api-python-client, OAuth2 authentication
  - **AC-1:** Uses google.oauth2.credentials.Credentials with refresh token from env
  - **AC-2:** Attachments encoded with base64.urlsafe_b64encode
  - **AC-3:** Raises GmailAPIError on API failure with full error response

- [ ] T065 [US7] Implement approval check in src/skills/send_email.py requiring approval for new contacts (not in address book), bulk sends (>5), attachments >1MB
  - **AC-1:** Address book loaded from Company_Handbook.md [Email] known_contacts
  - **AC-2:** Approval required for: new contacts, bulk >5 recipients, attachments >1MB
  - **AC-3:** Calls request_approval skill, blocks until approval file in Approved/

- [ ] T066 [US7] Implement --dry-run mode in src/skills/send_email.py logging without sending
  - **AC-1:** dry_run=True: no Gmail API calls, logs "DRY RUN: Would send email to {to}"
  - **AC-2:** Returns dict with status='dry_run'

- [ ] T067 [US7] Add circuit breaker to email API calls in src/skills/send_email.py
  - **AC-1:** Circuit breaker wraps send_email() and draft_email()
  - **AC-2:** When OPEN: raises CircuitBreakerOpen exception

- [ ] T068 [US7] Implement rate limiting in src/skills/send_email.py (max 100 calls/hour)
  - **AC-1:** Rate limit counter stored in SQLite (data/email_rate_limit.db)
  - **AC-2:** Rate limit exceeded: raises RateLimitExceeded exception

- [ ] T069 [US7] Add metrics emission: email_send_duration, email_send_count, email_send_errors
  - **AC-1:** Metrics include to_domain, dry_run tags

- [ ] T070 [US7] Write unit tests in tests/unit/test_send_email.py
  - **AC-1:** test_dry_run_no_api_call
  - **AC-2:** test_approval_required_for_new_contact
  - **AC-3:** test_circuit_breaker_trips_after_failures
  - **AC-4:** test_rate_limiting_enforced
  - **AC-5:** Gmail API calls mocked (no real sends)
  - **AC-6:** Test coverage ≥85% for send_email.py

- [ ] T070-INT Write integration tests in tests/integration/test_send_email_integration.py
  - **AC-1:** test_approval_workflow_integration
  - **AC-2:** Integration tests complete in <30 seconds

- [ ] T070-CHAOS Write chaos tests in tests/chaos/test_send_email_chaos.py
  - **AC-1:** test_api_failure_recovery
  - **AC-2:** test_dry_run_safe_under_failure

**Checkpoint:** User Story 7 complete - Email Action Skill independently functional

---

### User Story 8: LinkedIn Posting (S7) - Priority P2

**Goal:** Generate and post business content to LinkedIn with approval, rate limiting (1 post/day)

**Independent Test:** LinkedIn post generated from Business_Goals.md + Done/, approval required, post executed on approval

- [ ] T071 [P] [US8] Implement linkedin_posting skill in src/skills/linkedin_posting.py with generate_content() -> str, post_to_linkedin(content) -> dict methods
  - **AC-1:** generate_content() -> str method implemented
  - **AC-2:** post_to_linkedin(content: str) -> dict method implemented
  - **AC-3:** Return dict includes: post_id, status (posted/draft/failed), timestamp, url
  - **AC-4:** Extends BaseSkill class from src/skills/base_skill.py
  - **AC-5:** DEV_MODE validated before execution
  - **AC-6:** --dry-run flag supported via dry_run parameter
  - **AC-7:** When dry_run=True: logs "DRY RUN: Would post to LinkedIn" without browser action
  - **AC-8:** Correlation ID included in all logs

- [ ] T072 [US8] Implement content generation in src/skills/linkedin_posting.py combining Business_Goals.md + Done/ folder achievements
  - **AC-1:** _load_business_goals() -> str method reads vault/Business_Goals.md
  - **AC-2:** _load_recent_achievements() -> list[str] reads last 10 .md files from vault/Done/
  - **AC-3:** generate_content() combines goals + achievements into coherent post
  - **AC-4:** Post format: "🚀 {achievement} - {business_goal_connection}"
  - **AC-5:** Post length: 50-300 characters (LinkedIn optimal)
  - **AC-6:** Includes 2-3 relevant hashtags from Business_Goals.md [hashtags] list
  - **AC-7:** Content saved to draft file if not immediately posted

- [ ] T073 [US8] Implement Playwright browser automation in src/skills/linkedin_posting.py for LinkedIn posting
  - **AC-1:** Uses playwright.async_api for async browser automation
  - **AC-2:** Browser launched with headless=True, user_data_dir=vault/linkedin_session/
  - **AC-3:** _navigate_to_linkedin() navigates to https://www.linkedin.com/feed/
  - **AC-4:** _create_post(content: str) method: clicks "Start a post", enters content, clicks "Post"
  - **AC-5:** Post button selector: button[aria-label*="Share"]
  - **AC-6:** Post content entered via locator('div[contenteditable]').fill(content)
  - **AC-7:** Post confirmation: waits for "Your post has been shared" toast notification
  - **AC-8:** Returns post URL from feed after posting
  - **AC-9:** Raises LinkedInPostError on failure with screenshot saved to vault/Logs/linkedin_error_{timestamp}.png

- [ ] T074 [US8] Implement session recovery in src/skills/linkedin_posting.py with session storage in vault/linkedin_session/, auto-reauth on expiry
  - **AC-1:** _save_session() method saves browser context to vault/linkedin_session/storage.json
  - **AC-2:** Session saved via context.storage_state(path=vault/linkedin_session/storage.json)
  - **AC-3:** _load_session() method loads session on startup
  - **AC-4:** _is_session_valid() -> bool checks session not expired
  - **AC-5:** Session expiry detected when LinkedIn shows login page instead of feed
  - **AC-6:** Auto-reauth: raises LinkedInSessionExpired exception with re-authentication URL
  - **AC-7:** Dashboard.md updated with "LinkedIn session expired - please re-authenticate at linkedin.com"
  - **AC-8:** Session persists across application restarts

- [ ] T075 [US8] Implement rate limiting in src/skills/linkedin_posting.py (max 1 post/day, configurable)
  - **AC-1:** _check_rate_limit() -> bool method implemented
  - **AC-2:** Rate limit: max 1 post per 24 hours (configurable via Company_Handbook.md [LinkedIn] posts_per_day)
  - **AC-3:** Last post timestamp stored in SQLite (data/linkedin_posts.db)
  - **AC-4:** Returns True if post allowed, False if rate limited
  - **AC-5:** Rate limit exceeded: raises RateLimitExceeded exception
  - **AC-6:** Exception message: "LinkedIn rate limit exceeded (1 post/day) - retry after {reset_time}"
  - **AC-7:** Metrics emitted: linkedin_rate_limit_hits counter

- [ ] T076 [US8] Add circuit breaker to LinkedIn operations
  - **AC-1:** Circuit breaker wraps post_to_linkedin() method
  - **AC-2:** Uses circuit_breaker utility from src/utils/circuit_breaker.py
  - **AC-3:** failure_threshold=5, recovery_timeout=300 (5 minutes for LinkedIn)
  - **AC-4:** When OPEN: raises CircuitBreakerOpen exception without browser action
  - **AC-5:** State persists to data/circuit_breakers.db
  - **AC-6:** State changes logged with WARNING level
  - **AC-7:** Metrics emitted: linkedin_circuit_breaker_state_change counter

- [ ] T077 [US8] Add metrics emission: linkedin_post_duration, linkedin_post_count, linkedin_post_errors
  - **AC-1:** linkedin_post_duration histogram recorded per post attempt
  - **AC-2:** linkedin_post_count counter incremented on successful post
  - **AC-3:** linkedin_post_errors counter incremented on exception
  - **AC-4:** linkedin_content_generated counter incremented on generate_content()
  - **AC-5:** Metrics include content_type, dry_run tags
  - **AC-6:** Metrics persisted to SQLite and exposed via /metrics endpoint

- [ ] T078 [US8] Write unit tests in tests/unit/test_linkedin_posting.py
  - **AC-1:** test_content_generation_from_goals_and_done: verifies content combines both sources
  - **AC-2:** test_rate_limiting_enforced: verifies RateLimitExceeded after 1 post/day
  - **AC-3:** test_session_recovery_loads_saved_session: verifies storage.json loaded
  - **AC-4:** test_browser_automation_posts_content: verifies Playwright flow (mocked)
  - **AC-5:** test_session_expiry_detected: verifies LinkedInSessionExpired exception
  - **AC-6:** test_dry_run_no_browser_action: verifies dry_run=True skips browser
  - **AC-7:** test_circuit_breaker_trips_after_failures: verifies breaker opens
  - **AC-8:** All 7 test functions implemented and passing
  - **AC-9:** Test coverage ≥85% for linkedin_posting.py
  - **AC-10:** Playwright calls mocked (no real browser)

- [ ] T078-INT Write integration tests in tests/integration/test_linkedin_posting_integration.py
  - **AC-1:** test_end_to_end_post_generation_and_approval: generates content, creates approval, posts on approval
  - **AC-2:** test_session_persists_across_restarts: verifies storage.json survives restart
  - **AC-3:** All 2 integration tests implemented and passing
  - **AC-4:** Integration tests complete in <60 seconds

- [ ] T078-CHAOS Write chaos tests in tests/chaos/test_linkedin_posting_chaos.py
  - **AC-1:** test_browser_crash_recovery: kills browser process, verifies auto-restart
  - **AC-2:** test_session_expiry_handling: mocks expired session, verifies graceful halt and Dashboard.md update
  - **AC-3:** test_rate_limit_prevents_duplicate_posts: verifies rate limit enforced under concurrent calls
  - **AC-4:** All 3 chaos tests implemented and passing

**Checkpoint:** User Story 8 complete - LinkedIn Posting independently functional

---

### User Story 9: Dead Letter Queue Integration (S5 extension) - Priority P2

**Goal:** Archive failed actions to DLQ, support manual reprocessing

**Independent Test:** Failed actions archived to vault/Failed_Actions/, reprocessing supported

- [ ] T079 [P] [US9] Integrate approval handler with DLQ in src/approval_handler.py archiving failed actions after max retries
- [ ] T080 [US9] Implement DLQ monitoring in src/utils/dead_letter_queue.py with dashboard integration
- [ ] T081 [US9] Implement manual reprocessing in src/utils/dead_letter_queue.py allowing user to retry failed actions
- [ ] T082 [US9] Write tests for DLQ integration in tests/unit/test_dlq_integration.py

**Checkpoint:** User Story 9 complete - DLQ Integration independently functional

---

### Phase 4: Graceful Degradation

- [ ] T083 Implement graceful degradation across all components ensuring partial failures don't halt entire system
  - **AC-1:** **Watcher Level:** Each watcher (Gmail, WhatsApp, FileSystem) continues running when other watchers crash
  - **AC-2:** **Watcher Level:** Watcher catches all exceptions, logs error, continues to next iteration (no crash propagation)
  - **AC-3:** **Circuit Breaker Level:** When circuit breaker OPEN, watcher logs warning and skips check (doesn't crash)
  - **AC-4:** **Skill Level:** All skills catch exceptions and return error dict instead of raising (e.g., {"status": "error", "error": "message"})
  - **AC-5:** **Skill Level:** DEV_MODE=true prevents external actions but skill returns success with dry_run=True
  - **AC-6:** **Approval Level:** Approval handler continues monitoring when DLQ unavailable (logs warning, queues in memory)
  - **AC-7:** **Database Level:** SQLite failures logged, system continues with in-memory fallback (data loss warning logged)
  - **AC-8:** **File System Level:** File write failures trigger fallback to memory queue, retry on next successful write
  - **AC-9:** **Metrics Level:** Metrics collector failures don't halt execution (metrics lost, warning logged)
  - **AC-10:** **Health Check:** /health endpoint returns degraded status when non-critical component failing (status: "degraded")

- [ ] T084 Write chaos tests for graceful degradation in tests/chaos/test_graceful_degradation.py
  - **AC-1:** test_watcher_independence: crashes Gmail watcher, verifies WhatsApp and FileSystem continue running
  - **AC-2:** test_circuit_breaker_isolation: trips Gmail circuit breaker, verifies WhatsApp watcher unaffected
  - **AC-3:** test_skill_error_returns_dict: mocks skill failure, verifies error dict returned (no exception raised)
  - **AC-4:** test_sqlite_failure_continues_with_memory: mocks SQLite OperationalError, verifies in-memory fallback
  - **AC-5:** test_file_write_failure_queues_memory: mocks file write permission error, verifies memory queue used
  - **AC-6:** test_metrics_failure_doesnt_halt: mocks metrics collector raise, verifies execution continues
  - **AC-7:** test_health_endpoint_reports_degraded: simulates watcher down, verifies /health returns status: "degraded"
  - **AC-8:** test_dev_mode_prevents_external_calls: sets DEV_MODE=true, verifies no external API calls made
  - **AC-9:** All 8 chaos tests implemented and passing
  - **AC-10:** Chaos tests complete in <120 seconds

**Phase 4 Checkpoint:** Action Layer complete - All action skills functional with graceful degradation

---

## Phase 5: Production Readiness (12 hours)

**Purpose:** Health endpoint, load/endurance testing, documentation, deployment readiness

**Exit Criteria:**
- ✅ Health endpoint running (/health, /metrics, /ready)
- ✅ Load testing completed (100 emails burst)
- ✅ Endurance testing completed (7-day simulated)
- ✅ Runbook, DR plan, deployment checklist created
- ✅ All 85 tasks complete, 80%+ overall coverage

---

### User Story 10: Health Endpoint (ADR-007) - Priority P1

**Goal:** Expose health, metrics, readiness endpoints for external monitoring

**Independent Test:** GET /health returns JSON with component status, GET /metrics returns Prometheus format, GET /ready returns 503 if deps unhealthy

- [ ] T085 [P] [US10] Implement health endpoint in src/api/health_endpoint.py using FastAPI with /health, /metrics, /ready endpoints
- [ ] T086 [US10] Implement /health endpoint returning JSON status (status, version, uptime_seconds, components)
- [ ] T087 [US10] Implement /metrics endpoint returning Prometheus metrics format
- [ ] T088 [US10] Implement /ready endpoint returning 200 if all deps healthy, 503 otherwise
- [ ] T089 [US10] Add authentication token for /metrics (optional, configurable)
- [ ] T090 [US10] Add rate limiting to health endpoint (max 60 requests/minute)
- [ ] T091 [US10] Write unit + integration tests in tests/unit/test_health_endpoint.py, tests/integration/ (test_health_response, test_metrics_format, test_readiness_check, test_rate_limiting)

**Checkpoint:** User Story 10 complete - Health Endpoint independently functional

---

### User Story 11: Load Testing - Priority P2

**Goal:** Validate system handles burst load (100 emails in 5 minutes)

**Independent Test:** Load test completes with p95 < 2s, p99 < 5s, error rate < 1%

- [ ] T092 [P] [US11] Implement load test scenario in tests/load/test_burst_load.py simulating 100 emails in 5 minutes using locust
- [ ] T093 [US11] Implement metrics validation in tests/load/test_burst_load.py verifying p95 < 2s, p99 < 5s, error rate < 1%
- [ ] T094 [US11] Document load test results in docs/load-test-results.md with methodology, results, bottlenecks, recommendations

**Checkpoint:** User Story 11 complete - Load Testing documented

---

### User Story 12: Endurance Testing - Priority P2

**Goal:** Validate system runs 7 days without issues (simulated in 2 hours)

**Independent Test:** Endurance test completes with stable memory, no file descriptor leaks, no disk space leaks

- [ ] T095 [P] [US12] Implement endurance test scenario in tests/endurance/test_7day_simulation.py simulating 7 days in 2 hours
- [ ] T096 [US12] Implement memory leak detection in tests/endurance/test_7day_simulation.py verifying stable memory over time
- [ ] T097 [US12] Implement file descriptor leak detection verifying stable open file count
- [ ] T098 [US12] Implement disk space leak detection verifying log rotation works
- [ ] T099 [US12] Document endurance test results in docs/endurance-test-results.md

**Checkpoint:** User Story 12 complete - Endurance Testing documented

---

### User Story 13: Documentation - Priority P1

**Goal:** Create operational documentation (runbook, DR plan, deployment checklist)

**Independent Test:** All docs created, validated, actionable

- [ ] T100 [P] [US13] Create runbook in docs/runbook.md with common issues (watcher crashed, session expired, API quota exceeded, disk full), escalation policy
- [ ] T101 [US13] Create disaster recovery plan in docs/disaster-recovery.md with backup strategy (vault daily, credentials weekly, code continuous), restore procedures, RTO=4h, RPO=24h
- [ ] T102 [US13] Create deployment checklist in docs/deployment-checklist.md with pre-deployment (tests pass, quality gates pass, credentials rotated, backup created), post-deployment (smoke tests, monitoring active, logs flowing)
- [ ] T103 [US13] Create API documentation in docs/api-skills.md with OpenAPI-style spec for all 7+ skills
- [ ] T104 [US13] Create CHANGELOG.md with version history
- [ ] T105 [US13] Update README.md with Silver Tier setup instructions, badges

**Checkpoint:** User Story 13 complete - Documentation complete

---

### User Story 14: Production Certification - Priority P1

**Goal:** Final validation and certification

**Independent Test:** All production readiness checks pass

- [ ] T106 [P] [US14] Create production readiness certification in specs/002-silver-tier-functional-assistant/PRODUCTION_READY_CERTIFICATION.md with all critical/important items verified
- [ ] T107 [US14] Run full test suite with coverage report (pytest --cov=src --cov-report=html)
- [ ] T108 [US14] Run all quality gates (ruff, black, mypy --strict, bandit, isort)
- [ ] T109 [US14] Create 10 ADRs in history/adr/ (ADR-001 through ADR-010)
- [ ] T110 [US14] Final validation: all 85 tasks complete, 80%+ coverage, 0 quality gate errors

**Checkpoint:** User Story 14 complete - Production Ready

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T111 [P] Code cleanup and refactoring across all components
- [ ] T112 [P] Performance optimization (profile hot paths, optimize queries)
- [ ] T113 [P] Security hardening (review all inputs, validate all paths)
- [ ] T114 [P] Create skills index in src/skills/skills_index.md documenting all 7+ skills
- [ ] T115 [P] Create Dashboard.md template with all required sections

---

## Dependencies & Execution Order

### Phase Dependencies

| Phase | Dependencies | Blocks |
|-------|--------------|--------|
| Phase 1: Foundation | None | Phase 2 |
| Phase 2: Perception | Phase 1 | Phase 3 |
| Phase 3: Reasoning | Phase 2 | Phase 4 |
| Phase 4: Action | Phase 3 | Phase 5 |
| Phase 5: Production | Phase 4 | Production deployment |

### User Story Dependencies

| Story | Depends On | Independent Test |
|-------|------------|------------------|
| US1 (Gmail) | Phase 1 | ✅ Yes |
| US2 (WhatsApp) | Phase 1 | ✅ Yes |
| US3 (Process Manager) | Phase 1 | ✅ Yes |
| US4 (Plan Generation) | US1-US3 | ✅ Yes |
| US5 (Approval) | US4 | ✅ Yes |
| US6 (Briefing) | US4 | ✅ Yes |
| US7 (Email) | US5 | ✅ Yes |
| US8 (LinkedIn) | US5, US6 | ✅ Yes |
| US9 (DLQ) | US5 | ✅ Yes |
| US10 (Health) | All | ✅ Yes |
| US11 (Load Test) | US1-US10 | ✅ Yes |
| US12 (Endurance) | US1-US10 | ✅ Yes |
| US13 (Docs) | All | ✅ Yes |
| US14 (Cert) | All | ✅ Yes |

### Parallel Opportunities

**Phase 1:** T001-T004 can run in parallel (vault + templates), T005-T012 can run in parallel (utilities + tests)

**Phase 2:** US1, US2, US3 can be implemented in parallel by different developers

**Phase 3:** US4, US5, US6 can be implemented in parallel

**Phase 4:** US7, US8, US9 can be implemented in parallel

**Phase 5:** US10, US11, US12, US13 can be implemented in parallel

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

1. Complete Phase 1: Foundation (T001-T012)
2. Complete Phase 2: Perception - US1, US2, US3 only (T013-T041)
3. **STOP and VALIDATE:** All watchers running with Process Manager
4. Deploy MVP: Multi-source monitoring operational

### Incremental Delivery

1. **Milestone 1:** Phase 1 + Phase 2 → Watchers operational (26 hours)
2. **Milestone 2:** + Phase 3 → Plan generation + Approval workflow (40 hours)
3. **Milestone 3:** + Phase 4 → Action skills (Email, LinkedIn) operational (58 hours)
4. **Milestone 4:** + Phase 5 → Production ready (70 hours)

### Parallel Team Strategy

With 2 developers:
- Developer A: US1 (Gmail), US4 (Plan), US7 (Email), US10 (Health)
- Developer B: US2 (WhatsApp), US5 (Approval), US8 (LinkedIn), US11 (Load Test)
- Together: Phase 1, US3 (Process Manager), US6 (Briefing), US9 (DLQ), US12-US14

With 3 developers:
- Developer A: Perception Layer (US1, US2, US3)
- Developer B: Reasoning Layer (US4, US5, US6)
- Developer C: Action Layer (US7, US8, US9)
- Together: Phase 1, Phase 5

---

## Quality Gates (ALL Tasks)

Every task MUST pass:

| Gate | Command | Requirement |
|------|---------|-------------|
| Linting | `ruff check src/[module]/ --select E,F,W,I,N,B,C4` | 0 errors |
| Formatting | `black --check src/[module]/ --line-length 100` | 0 errors |
| Type Checking | `mypy --strict src/[module]/ --no-error-summary` | 0 errors |
| Security | `bandit -r src/[module]/ --format custom` | 0 high-severity |
| Coverage | `pytest tests/unit/test_[module].py --cov=[module] --cov-fail-under=85` | 85%+ |
| Import Order | `isort --check-only src/[module]/` | 0 errors |

---

## Production Readiness Checks (Production Critical Tasks)

All production critical tasks (marked Production Critical: YES) MUST verify:

- [ ] Circuit breaker implemented (if external API call)
- [ ] Metrics emitted (duration, errors, status codes)
- [ ] Logging with correlation_id (JSON format)
- [ ] Error handling with typed exceptions
- [ ] Graceful degradation (failure doesn't halt system)
- [ ] --dry-run mode supported (if action skill)
- [ ] Rate limiting implemented (if applicable)
- [ ] Session expiry detection (if session-based)
- [ ] Dead letter queue integration (if action can fail)

---

## Appendix A: Test File Index

| Component | Test File | Test Count |
|-----------|-----------|------------|
| Circuit Breaker | tests/unit/test_circuit_breaker.py | 12 |
| Metrics Collector | tests/unit/test_metrics_collector.py | 6 |
| Log Aggregator | tests/unit/test_log_aggregator.py | 6 |
| Dead Letter Queue | tests/unit/test_dead_letter_queue.py | 5 |
| Gmail Watcher | tests/unit/test_gmail_watcher.py | 10 |
| Gmail Watcher Integration | tests/integration/test_gmail_watcher_integration.py | 3 |
| Gmail Watcher Chaos | tests/chaos/test_gmail_watcher_chaos.py | 4 |
| WhatsApp Watcher | tests/unit/test_whatsapp_watcher.py | 5+ |
| Process Manager | tests/unit/test_process_manager.py | 6+ |
| Create Plan | tests/unit/test_create_plan.py | 5+ |
| Approval Handler | tests/unit/test_approval_handler.py | 5+ |
| Generate Briefing | tests/unit/test_generate_briefing.py | 3+ |
| Send Email | tests/unit/test_send_email.py | 6+ |
| LinkedIn Posting | tests/unit/test_linkedin_posting.py | 5+ |
| Health Endpoint | tests/unit/test_health_endpoint.py | 4+ |
| Load Tests | tests/load/test_burst_load.py | 2+ |
| Endurance Tests | tests/endurance/test_7day_simulation.py | 5+ |

**Total Tests:** 100+ (unit, integration, chaos, load, endurance)

---

## Appendix B: File Structure

```
FTE/
├── src/
│   ├── base_watcher.py              [Bronze - Existing]
│   ├── filesystem_watcher.py        [Bronze - Extend]
│   ├── process_manager.py           [T031-T038]
│   ├── approval_handler.py          [T052-T055, T079]
│   ├── base_skill.py                [T061-T062]
│   ├── watchers/
│   │   ├── gmail_watcher.py         [T013-T022]
│   │   └── whatsapp_watcher.py      [T023-T030]
│   ├── skills/
│   │   ├── create_plan.py           [T042-T048]
│   │   ├── request_approval.py      [T049-T051]
│   │   ├── generate_briefing.py     [T056-T060]
│   │   ├── send_email.py            [T063-T070]
│   │   ├── linkedin_posting.py      [T071-T078]
│   │   └── skills_index.md          [T114]
│   ├── utils/
│   │   ├── circuit_breaker.py       [T005-T006]
│   │   └── dead_letter_queue.py     [T011-T012, T080-T082]
│   ├── metrics/
│   │   └── collector.py             [T007-T008]
│   ├── logging/
│   │   └── log_aggregator.py        [T009-T010]
│   ├── scheduler/
│   │   ├── daily_briefing.py        [T056-T060]
│   │   └── weekly_audit.py          [T056-T060]
│   └── api/
│       └── health_endpoint.py       [T085-T091]
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── chaos/
│   ├── load/
│   └── endurance/
├── data/
│   ├── circuit_breakers.db          [Runtime]
│   ├── processed_emails.db          [Runtime]
│   └── failed_actions.db            [Runtime]
├── vault/
│   ├── Inbox/                       [Bronze]
│   ├── Needs_Action/                [Bronze - Extended]
│   ├── Plans/                       [T001]
│   ├── Pending_Approval/            [T001]
│   ├── Approved/                    [T001]
│   ├── Rejected/                    [T001]
│   ├── Done/                        [Bronze]
│   ├── Briefings/                   [T001]
│   ├── Templates/                   [T001-T004]
│   ├── Failed_Actions/              [T001]
│   ├── Logs/                        [Bronze]
│   └── Dashboard.md                 [Bronze - Extended]
└── docs/
    ├── runbook.md                   [T100]
    ├── disaster-recovery.md         [T101]
    ├── deployment-checklist.md      [T102]
    ├── api-skills.md                [T103]
    ├── load-test-results.md         [T094]
    └── endurance-test-results.md    [T099]
```

---

## Appendix C: Production Readiness Master Checklist

### Foundation (Phase 1)
- [ ] T001-T004: Vault structure extended, templates created
- [ ] T005-T006: Circuit breaker with SQLite persistence, 90%+ coverage
- [ ] T007-T008: Metrics collector with Prometheus + SQLite
- [ ] T009-T010: Log aggregator with rotation, compression, retention
- [ ] T011-T012: Dead letter queue operational

### Perception (Phase 2)
- [ ] T013-T022: Gmail Watcher operational (2-min interval, circuit breaker, metrics)
- [ ] T023-T030: WhatsApp Watcher operational (30-sec interval, keyword filtering, session preservation)
- [ ] T031-T038: Process Manager operational (auto-restart within 10s, restart limits)
- [ ] T039-T041: FileSystem Watcher extended with metrics + circuit breaker

### Reasoning (Phase 3)
- [ ] T042-T048: create_plan skill operational (YAML frontmatter, status tracking)
- [ ] T049-T055: request_approval skill + approval handler (24-hour expiry, 5-sec detection)
- [ ] T056-T060: generate_briefing skill operational (daily + weekly)
- [ ] T061-T062: Base skill class with DEV_MODE, --dry-run, correlation_id

### Action (Phase 4)
- [ ] T063-T070: send_email skill operational (Gmail API, approval for new contacts, --dry-run)
- [ ] T071-T078: linkedin_posting skill operational (Playwright, session recovery, 1 post/day)
- [ ] T079-T082: DLQ integration operational (archive failed, manual reprocess)
- [ ] T083-T084: Graceful degradation implemented

### Production (Phase 5)
- [ ] T085-T091: Health endpoint operational (/health, /metrics, /ready)
- [ ] T092-T094: Load testing completed (100 emails burst, p95 < 2s)
- [ ] T095-T099: Endurance testing completed (7-day simulated, no leaks)
- [ ] T100-T105: Documentation complete (runbook, DR, deployment, API, CHANGELOG)
- [ ] T106-T110: Production certification complete (all checks pass)
- [ ] T111-T115: Polish complete (cleanup, optimization, skills index)

---

**Total Task Count:** 115 tasks (T001-T115)

**Task Breakdown:**
- Phase 1: T001-T012 (12 tasks) - Foundation utilities
- Phase 2: T013-T041 (29 tasks) - Perception layer (watchers + process manager)
- Phase 3: T042-T062 (21 tasks) - Reasoning layer (skills)
- Phase 4: T063-T084 (22 tasks) - Action layer (email, LinkedIn, DLQ)
- Phase 5: T085-T115 (31 tasks) - Production readiness (health, tests, docs)

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [US#] label = maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at phase checkpoints to validate independently
- All tasks must pass 6 quality gates before marking complete
- Production critical tasks require additional production readiness checks
