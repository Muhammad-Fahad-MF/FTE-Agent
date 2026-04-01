# Skills Index: FTE-Agent Silver Tier

**Version**: 2.0.0  
**Last Updated**: 2026-04-02  
**Total Skills**: 7

---

## Overview

This document indexes all Python Skills available in the FTE-Agent Silver Tier. Skills are reusable functions that can be called via direct Python import, CLI wrappers, or Qwen Code CLI.

---

## Core Skills

### 1. `check_dev_mode`

**Location**: `src/skills.py`  
**Purpose**: Validate DEV_MODE environment variable  
**Signature**: `def check_dev_mode() -> bool`

---

### 2. `create_action_file`

**Location**: `src/skills.py`  
**Purpose**: Create action file in `vault/Needs_Action/`  
**Signature**: `def create_action_file(file_type: str, source: str, content: str = "", dry_run: bool = False) -> str`

---

### 3. `log_audit`

**Location**: `src/skills.py`  
**Purpose**: Write audit log entry  
**Signature**: `def log_audit(action: str, details: dict[str, Any], level: str = "INFO", dry_run: bool = False) -> None`

---

### 4. `validate_path`

**Location**: `src/skills.py`  
**Purpose**: Validate path is within vault  
**Signature**: `def validate_path(file_path: str, vault_path: str) -> str`

---

### 5. `create_alert_file`

**Location**: `src/skills.py`  
**Purpose**: Create alert file for critical errors  
**Signature**: `def create_alert_file(file_type: str, source: str, details: dict[str, Any], severity: str = "critical") -> Path`

---

## Action Skills

### 6. `send_email`

**Location**: `src/skills/send_email.py`  
**Purpose**: Send email via Gmail API  
**Signature**: `async def send_email(to: str, subject: str, body: str, cc: list[str] = None, attachments: list[str] = None, dry_run: bool = False) -> dict[str, Any]`

---

### 7. `linkedin_posting`

**Location**: `src/skills/linkedin_posting.py`  
**Purpose**: Post to LinkedIn  
**Signature**: `async def linkedin_posting(content: str, visibility: str = "public", dry_run: bool = False) -> dict[str, Any]`

---

## Planning Skills

### 8. `create_plan`

**Location**: `src/skills/create_plan.py`  
**Purpose**: Generate plan from action file  
**Signature**: `def create_plan(objective: str, source_file: str, estimated_steps: int = 10, requires_approval: bool = True, dry_run: bool = False) -> dict[str, Any]`

---

### 9. `request_approval`

**Location**: `src/skills/request_approval.py`  
**Purpose**: Request approval for action  
**Signature**: `def request_approval(action_type: str, action_details: dict[str, Any], risk_level: str = "medium", reason: str = "", dry_run: bool = False) -> dict[str, Any]`

---

### 10. `generate_briefing`

**Location**: `src/skills/generate_briefing.py`  
**Purpose**: Generate daily/weekly briefing  
**Signature**: `def generate_briefing(briefing_type: str, period: str, dry_run: bool = False) -> dict[str, Any]`

---

## Utility Skills

### 11. `PersistentCircuitBreaker`

**Location**: `src/utils/circuit_breaker.py`  
**Purpose**: Circuit breaker with SQLite persistence  
**Class**: `PersistentCircuitBreaker`

---

### 12. `MetricsCollector`

**Location**: `src/metrics/collector.py`  
**Purpose**: Prometheus metrics with SQLite persistence  
**Class**: `MetricsCollector`

---

### 13. `LogAggregator`

**Location**: `src/logging/log_aggregator.py`  
**Purpose**: JSON log aggregation with rotation  
**Class**: `LogAggregator`

---

### 14. `DeadLetterQueue`

**Location**: `src/utils/dead_letter_queue.py`  
**Purpose**: Archive and reprocess failed actions  
**Class**: `DeadLetterQueue`

---

## Usage Examples

### Import Skill

```python
from src.skills import create_action_file

path = create_action_file(
    file_type="email",
    source="gmail:123",
    content="Urgent message"
)
```

### CLI Usage

```bash
python -c "from src.skills import log_audit; log_audit('test', {'key': 'value'})"
```

### Qwen Code CLI

```bash
qwen "Use create_action_file to create an email action file"
```

---

**Total Skills**: 14 (5 core, 2 action, 3 planning, 4 utility)  
**Documentation**: See `docs/api-skills.md` for full API specification
