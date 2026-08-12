# AURELIX Evidence & Verification Engine V1

The Research Engine must not turn a generated claim into institutional knowledge merely because an LLM produced it.

## Evidence model

Each evidence item records:

- source reference
- claim
- relation: SUPPORTS, CONTRADICTS or CONTEXT
- quality score

## Verification states

```text
UNVERIFIED
INCONCLUSIVE
SUPPORTED
CONFLICTED
```

A conflicted claim is never silently promoted to fact.

## Architecture

```text
External sources
      ↓
Evidence
      ↓
Claim verification
      ↓
Support / contradiction analysis
      ↓
Confidence + status
      ↓
Research Finding
      ↓
Academy (only when policy permits)
```

The confidence score is a decision-support signal, not a proof of truth. Source independence, recency, authority and domain-specific validation should be added as future scoring dimensions.

This design follows the broader principle of continuous AI risk management and measurable verification advocated by NIST, while applying least privilege and complete mediation to agent tool use as recommended by OWASP. citeturn0search7turn0search1
