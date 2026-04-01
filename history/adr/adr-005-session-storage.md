# ADR-005: Session Storage

**Date**: 2026-03-19  
**Status**: Proposed  
**Author**: FTE-Agent Team

---

## Context

WhatsApp and LinkedIn require session persistence across restarts.

## Options Considered

### Option 1: File-based with Encryption (Recommended)

Store session cookies in encrypted files.

**Pros**:
- Simple implementation
- Persists across restarts
- Can encrypt sensitive data

**Cons**:
- File system dependency
- Encryption key management

### Option 2: SQLite Database

Store sessions in database.

**Pros**:
- Centralized storage
- Transaction support

**Cons**:
- Overkill for simple session data
- More complex

### Option 3: Keyring/Keychain

Use OS credential storage.

**Pros**:
- Secure
- OS-managed

**Cons**:
- Platform-specific
- Size limits

## Decision

**Option 1: File-based with Encryption**

- WhatsApp: `vault/whatsapp_session/storage.json` (Playwright storage state)
- LinkedIn: `vault/linkedin_session/cookies.json`
- Sensitive data encrypted with key from `.env`

## Consequences

- ✅ Simple and effective
- ✅ Cross-platform
- ⚠️ Must protect session files

---

**Review Date**: 2026-07-02
