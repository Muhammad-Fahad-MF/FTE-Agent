# ADR-003: LinkedIn Posting

**Date**: 2026-03-19  
**Status**: Proposed  
**Author**: FTE-Agent Team

---

## Context

Silver Tier needs to post to LinkedIn for personal branding. LinkedIn has no public API for posting.

## Options Considered

### Option 1: Playwright with Session Recovery (Recommended)

Use browser automation with session persistence.

**Pros**:
- Works without official API
- Session persists across restarts
- Full control over posting

**Cons**:
- Browser dependency
- Session expiry handling required
- Rate limiting (1 post/day)

### Option 2: LinkedIn API (Enterprise)

Use LinkedIn Marketing API.

**Pros**:
- Official support
- Reliable

**Cons**:
- Enterprise only
- Complex setup
- Cost

### Option 3: Third-party Service (Buffer, Hootsuite)

Use social media management tools.

**Pros**:
- Multi-platform
- Scheduling

**Cons**:
- Cost
- External dependency
- Limited customization

## Decision

**Option 1: Playwright with Session Recovery**

Implementation in `src/skills/linkedin_posting.py`:
- Playwright with Chromium
- Session saved to `vault/linkedin_session/`
- Auto-recovery on restart
- 1 post/day limit
- `--dry-run` mode

## Consequences

- ✅ No API key required
- ✅ Session persists
- ⚠️ Requires browser installation
- ⚠️ Session expiry detection needed

---

**Review Date**: 2026-07-02
