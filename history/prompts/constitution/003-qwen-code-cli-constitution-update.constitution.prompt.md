---
id: 003
title: Qwen Code CLI Constitution Update
stage: constitution
date: 2026-03-07
surface: agent
model: qwen3-coder-plus
feature: none
branch: main
user: Imperial_Legend
command: /sp.constitution Update for Qwen Code CLI + Python Skills pattern
labels: ["constitution","qwen-code-cli","python-skills","free-tier"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - QWEN.md
  - .specify/memory/constitution.md
tests:
  - N/A (constitution amendment - no tests run)
---

## Prompt

Update both QWEN.md and constitution for the new plan:
- Replace Claude Code with Qwen Code CLI (free OAuth tier - 1,000 calls/day)
- Replace MCP servers with Python Skills pattern (src/skills.py)
- Document that Bronze tier doesn't need MCP (file operations only)
- Add Qwen Code CLI installation and authentication instructions
- Update Technology Stack, Directory Structure, Safety Validation Checklist
- Add new principle XIII: AI Reasoning Engine & Python Skills Pattern

## Response snapshot

Updated both files to reflect Qwen Code CLI as the free AI reasoning engine:

**QWEN.md Changes:**
- Added AI Engine section with Qwen Code CLI installation (npm install -g @qwen-code/qwen-code)
- Documented OAuth authentication for 1,000 free calls/day
- Added MCP limitation notice with Python Skills workaround
- Command equivalents table (Claude Code → Qwen Code CLI)
- Development workflow updated for Spec-Driven + Python Skills pattern

**Constitution v3.0.0 Changes:**
- Principle III: "Claude Code" → "Qwen Code CLI", "Agent Skills" → "Python Skills"
- Principle IV: "orchestrator→Claude" → "orchestrator→Qwen"
- Principle IX: Removed MCP server contract tests, added Python Skills schemas
- NEW Principle XIII: AI Reasoning Engine & Python Skills Pattern
  - Qwen Code CLI mandatory for AI-assisted development
  - Python Skills in src/skills.py replace MCP servers
  - Bronze/Silver/Gold tier integration paths defined
- Technology Stack: Claude Code → Qwen Code CLI, MCP servers → Python Skills with direct integrations
- Directory Structure: Added src/skills.py, scripts/ralph-loop.bat
- Safety Validation: Added Qwen Code CLI installation check
- Emergency Procedures: Added Qwen API rate limit workaround

**Key Architecture Decision:**
Python Skills pattern enables free development with Qwen Code CLI while maintaining extensibility. Bronze tier needs only file I/O (no external APIs). Silver/Gold use direct Python integrations (smtplib, requests, playwright) instead of MCP.

## Outcome

- ✅ Impact: Constitution v3.0.0 ratified with Qwen Code CLI + Python Skills pattern - 100% free development stack
- 🧪 Tests: N/A (constitution amendment - validation via grep for placeholder tokens)
- 📁 Files: QWEN.md, .specify/memory/constitution.md updated
- 🔁 Next prompts: Create src/skills.py, scripts/ralph-loop.bat, README.md with setup instructions
- 🧠 Reflection: Removing MCP dependency enables free development while maintaining architectural integrity

## Evaluation notes (flywheel)

- Failure modes observed: None - file edits completed successfully
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
