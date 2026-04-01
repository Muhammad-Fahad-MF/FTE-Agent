# FTE-Agent: Silver Tier Functional Assistant

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/your-org/fte-agent/releases)
[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-passing-green.svg)](https://github.com/your-org/fte-agent/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%25-green.svg)](https://github.com/your-org/fte-agent/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Your AI-Powered Employee for Automated Task Management**

FTE-Agent is a production-grade functional assistant that monitors multiple sources (Gmail, WhatsApp, FileSystem), generates action plans, requests human approval, and executes actions (Email, LinkedIn) on your behalf.

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Testing](#testing)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### Silver Tier (v2.0.0)

#### Multi-Source Monitoring 📥
- **Gmail Watcher**: Monitor emails every 2 minutes with OAuth2 authentication
- **WhatsApp Watcher**: Monitor messages every 30 seconds with keyword filtering
- **FileSystem Watcher**: Monitor folders for new files every 60 seconds
- **Process Manager**: Auto-restart crashed watchers within 10 seconds

#### Human-in-the-Loop Approval 👤
- **Approval Workflow**: 24-hour expiry with risk classification
- **Auto-Detection**: 5-second detection of approval file moves
- **Dead Letter Queue**: Archive and reprocess failed approvals

#### Action Skills 🎯
- **Send Email**: Gmail API integration with attachments, CC, BCC
- **LinkedIn Posting**: Browser automation with session recovery
- **Generate Briefing**: Daily (8 AM) and weekly (Sunday 10 PM) summaries
- **Create Plan**: YAML-based plan generation with status tracking

#### Production-Grade Features 🏭
- **Health Endpoint**: `/health`, `/metrics`, `/ready` for monitoring
- **Circuit Breakers**: Prevent cascade failures (5 failures → trip, 60s → reset)
- **Metrics Collection**: Prometheus-format metrics with SQLite persistence
- **Log Aggregation**: JSON logs with rotation, compression, retention
- **Rate Limiting**: Gmail (100/hour), WhatsApp (60/hour), LinkedIn (1/day)

### Coming in Gold Tier (v3.0.0)
- Multi-tenant support
- Advanced analytics dashboard
- Slack/Teams integration
- ML-based action prioritization
- Mobile app for approvals

---

## Quick Start

### Prerequisites
- Python 3.13+
- Windows 10/11 or Linux/Mac
- Gmail account with OAuth2 setup
- WhatsApp Web account

### 5-Minute Setup

```bash
# 1. Clone repository
git clone https://github.com/your-org/fte-agent.git
cd fte-agent/FTE

# 2. Install dependencies
pip install -r requirements.txt
playwright install  # Install browser for WhatsApp/LinkedIn

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Authenticate OAuth2 services
python src/watchers/gmail_watcher.py --reauth
python src/watchers/whatsapp_watcher.py --reauth

# 5. Start the system
python src/process_manager.py --start

# 6. Verify health
curl http://localhost:8000/health
```

### Verify Installation

```bash
# All watchers should be UP
python src/process_manager.py --status

# Expected output:
# Gmail Watcher: UP (last check: 10 seconds ago)
# WhatsApp Watcher: UP (last check: 5 seconds ago)
# FileSystem Watcher: UP (last check: 30 seconds ago)
```

---

## Installation

### System Requirements

| Component | Requirement | Recommended |
|-----------|-------------|-------------|
| OS | Windows 10/11, Linux, Mac | Windows 11 |
| Python | 3.13+ | 3.13.2 |
| RAM | 8GB | 16GB |
| Disk | 256GB free | 512GB SSD |
| Network | Internet access | Broadband |

### Step-by-Step Installation

#### 1. Install Python

**Windows**:
```powershell
# Download from https://python.org/downloads
# Run installer, check "Add Python to PATH"
python --version  # Should show 3.13+
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install python3.13 python3.13-venv python3-pip
python3 --version
```

**Mac**:
```bash
brew install python@3.13
python3 --version
```

#### 2. Clone Repository

```bash
git clone https://github.com/your-org/fte-agent.git
cd fte-agent/FTE
```

#### 3. Create Virtual Environment (Recommended)

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### 4. Install Dependencies

```bash
pip install -r requirements.txt
playwright install  # Install Chromium, Firefox, WebKit
```

#### 5. Setup Environment Variables

```bash
# Copy example
cp .env.example .env

# Edit .env with your settings:
# - DEV_MODE=true (for development)
# - VAULT_PATH=/path/to/vault
# - LOG_LEVEL=INFO
```

#### 6. Authenticate Services

**Gmail OAuth2**:
```bash
# Follow prompts to authenticate
python src/watchers/gmail_watcher.py --reauth

# Token saved to ~/.credentials/gmail-token.json
```

**WhatsApp Session**:
```bash
# Scan QR code with WhatsApp mobile app
python src/watchers/whatsapp_watcher.py --reauth

# Session saved to vault/whatsapp_session/storage.json
```

**LinkedIn Session**:
```bash
# Login via browser
python src/skills/linkedin_posting.py --reauth

# Session saved to vault/linkedin_session/
```

---

## Configuration

### Environment Variables (.env)

```ini
# Development Mode (true/false)
# When true, external actions are blocked
DEV_MODE=true

# Vault Path (absolute path)
VAULT_PATH=H:\Programming\FTE-Agent\FTE\vault

# Log Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Gmail API Credentials
GMAIL_CREDENTIALS_FILE=~/.credentials/gmail-token.json

# Health Endpoint
HEALTH_ENDPOINT_HOST=localhost
HEALTH_ENDPOINT_PORT=8000
```

### Company Handbook (Company_Handbook.md)

```ini
[Gmail]
check_interval_seconds = 120
rate_limit_calls_per_hour = 100

[WhatsApp]
check_interval_seconds = 30
keywords = urgent, asap, invoice, payment, help

[FileSystem]
check_interval_seconds = 60
source_folder = H:\Programming\FTE-Agent\FTE\vault\Inbox

[ProcessManager]
health_check_interval_seconds = 10
restart_limit_per_hour = 3
memory_threshold_mb = 200

[CircuitBreaker]
failure_threshold = 5
recovery_timeout_seconds = 60
```

---

## Usage

### Start the System

```bash
# Start all watchers
python src/process_manager.py --start

# Check status
python src/process_manager.py --status

# Stop all watchers
python src/process_manager.py --stop
```

### Monitor Health

```bash
# Overall health
curl http://localhost:8000/health

# Prometheus metrics
curl http://localhost:8000/metrics

# Readiness check
curl http://localhost:8000/ready
```

### View Dashboard

Open `vault/Dashboard.md` in any Markdown editor (e.g., Obsidian, VS Code).

### Process Action Files

1. **New items appear in**: `vault/Needs_Action/`
2. **Review and move to**: `vault/Plans/` (for plan generation)
3. **After approval**: Move to `vault/Pending_Approval/`
4. **After execution**: Move to `vault/Done/`

### Generate Briefings

```bash
# Daily briefing
python src/skills/generate_briefing.py --type daily

# Weekly briefing
python src/skills/generate_briefing.py --type weekly

# Output: vault/Briefings/daily_YYYYMMDD.md
```

---

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     FTE-Agent System                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Gmail     │  │  WhatsApp   │  │  FileSystem │         │
│  │  Watcher    │  │   Watcher   │  │   Watcher   │         │
│  │  (2 min)    │  │  (30 sec)   │  │  (60 sec)   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┴────────────────┘                 │
│                          │                                  │
│                   ┌──────▼──────┐                           │
│                   │   Process   │                           │
│                   │   Manager   │                           │
│                   │ (Health Mon)│                           │
│                   └──────┬──────┘                           │
│                          │                                  │
│         ┌────────────────┼────────────────┐                 │
│         │                │                │                 │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐         │
│  │   Create    │  │   Request   │  │   Generate  │         │
│  │    Plan     │  │  Approval   │  │  Briefing   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│  ┌──────▼──────┐  ┌──────▼──────┐        │                 │
│  │   Send      │  │  LinkedIn   │        │                 │
│  │   Email     │  │  Posting    │        │                 │
│  └─────────────┘  └─────────────┘        │                 │
│                                          │                 │
│  ┌──────────────────────────────────────▼──────┐           │
│  │           Health Endpoint                   │           │
│  │  /health  /metrics  /ready                  │           │
│  └─────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### Vault Structure

```
vault/
├── Inbox/                    # Incoming files (FileSystem Watcher)
├── Needs_Action/             # New action files from watchers
├── Plans/                    # Generated plans
├── Pending_Approval/         # Awaiting approval
├── Approved/                 # Approved actions
├── Rejected/                 # Rejected actions
├── Briefings/                # Daily/weekly briefings
├── Templates/                # Plan, approval, DLQ templates
├── Failed_Actions/           # Dead letter queue files
├── Logs/                     # JSON audit logs
├── whatsapp_session/         # WhatsApp session storage
├── linkedin_session/         # LinkedIn session storage
└── Dashboard.md              # System status dashboard
```

---

## Testing

### Run All Tests

```bash
cd FTE

# Unit tests
pytest tests/unit/ -v --cov=src

# Integration tests
pytest tests/integration/ -v

# Chaos tests
pytest tests/chaos/ -v

# Load tests
pytest tests/load/ -v

# Endurance tests
pytest tests/endurance/ -v
```

### Quality Gates

```bash
# Linting
ruff check src/ tests/ --select E,F,W,I,N,B,C4

# Formatting
black --check src/ tests/ --line-length 100

# Type checking
mypy --strict src/ --no-error-summary

# Security scan
bandit -r src/ --format custom

# Import order
isort --check-only src/ tests/
```

### Test Coverage Requirements

| Test Type | Coverage | Command |
|-----------|----------|---------|
| Unit Tests | ≥85% per module | `pytest tests/unit/ --cov=src` |
| Integration Tests | End-to-end flows | `pytest tests/integration/` |
| Chaos Tests | Failure recovery | `pytest tests/chaos/` |
| Load Tests | p95 <2s, p99 <5s | `pytest tests/load/` |
| Endurance Tests | 7-day simulation | `pytest tests/endurance/` |

---

## Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| **Runbook** | `docs/runbook.md` | Troubleshooting, escalation |
| **Disaster Recovery** | `docs/disaster-recovery.md` | Backup/restore procedures |
| **Deployment Checklist** | `docs/deployment-checklist.md` | Pre/post deployment steps |
| **API Skills** | `docs/api-skills.md` | Skill specifications |
| **Load Test Results** | `docs/load-test-results.md` | Performance benchmarks |
| **Endurance Test Results** | `docs/endurance-test-results.md` | Long-run stability |
| **CHANGELOG** | `FTE/CHANGELOG.md` | Version history |

---

## Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a branch**: `git checkout -b feature/my-feature`
3. **Make changes** following the spec-driven workflow
4. **Run tests**: Ensure all quality gates pass
5. **Submit PR**: Include test results and CHANGELOG entry

### Code Standards

- **Type Annotations**: Required for all functions
- **Docstrings**: Google-style with Args, Returns, Raises
- **Testing**: 85%+ coverage per module
- **Linting**: 0 errors from ruff, black, mypy, bandit

### Spec-Driven Development

```
Spec (spec.md)
    ↓
Plan (plan.md)
    ↓
Tasks (tasks.md)
    ↓
Implementation
    ↓
Tests (Red → Green → Refactor)
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

### Getting Help

- **Documentation**: Browse `docs/` directory
- **Issues**: [GitHub Issues](https://github.com/your-org/fte-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/fte-agent/discussions)

### Reporting Bugs

1. Check existing issues
2. Include: Python version, OS, error logs, reproduction steps
3. Use bug report template

### Feature Requests

1. Check existing requests
2. Describe use case and expected behavior
3. Use feature request template

---

## Acknowledgments

- Built with [SpecKit Plus](https://github.com/your-org/speckit-plus)
- Inspired by [Keep a Changelog](https://keepachangelog.com)
- Testing with [pytest](https://docs.pytest.org)
- Monitoring with [Prometheus](https://prometheus.io)

---

**Version**: 2.0.0 (Silver Tier)  
**Release Date**: 2026-04-02  
**Status**: ✅ Production Ready  
**Next Release**: Gold Tier (Q3 2026)
