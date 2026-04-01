# ADR-002: Email Integration

**Date**: 2026-03-19  
**Status**: Proposed  
**Author**: FTE-Agent Team

---

## Context

The Silver Tier needs to send emails via Gmail. We need a secure, reliable method with proper error handling.

## Options Considered

### Option 1: Python Skill with Circuit Breaker (Recommended)

Use Gmail API via `google-api-python-client` with circuit breaker protection.

**Pros**:
- Official Gmail API support
- OAuth2 authentication
- Circuit breaker prevents cascade failures
- Rate limiting built-in

**Cons**:
- OAuth2 setup complexity
- API quota limits (100 calls/hour)

### Option 2: SMTP with TLS

Use `smtplib` for direct email sending.

**Pros**:
- Simple setup
- No API quotas

**Cons**:
- Less secure (password-based)
- No retry logic
- Spam folder risk

### Option 3: Third-party Service (SendGrid, Mailgun)

Use external email service.

**Pros**:
- High deliverability
- Analytics

**Cons**:
- External dependency
- Cost
- Additional setup

## Decision

**Option 1: Python Skill with Circuit Breaker**

Implementation in `src/skills/send_email.py`:
- Gmail API with OAuth2
- Circuit breaker (5 failures → trip, 60s → reset)
- Rate limiting (50 emails/hour)
- `--dry-run` mode
- Approval required for new contacts

## Consequences

- ✅ Secure OAuth2 authentication
- ✅ Resilient with circuit breaker
- ⚠️ Requires Google Cloud Console setup

---

**Review Date**: 2026-07-02
