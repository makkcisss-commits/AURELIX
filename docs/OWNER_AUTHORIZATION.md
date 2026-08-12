# Owner Authorization Contract

AURELIX separates **authentication**, **authorization**, and **execution**.

## Current core boundary

The Python core represents an explicit owner approval as a scoped `OwnerApproval` record. It can authorize one specific `DecisionRequest`, optionally with an expiration time and a maximum financial amount.

The core record is **not** proof of identity. The future control-plane API must authenticate the owner before creating an approval. Authentication credentials, sessions, passkeys, MFA, and secrets must remain outside the domain model and must never be committed to this repository.

## Approval lifecycle

```text
REQUEST
  ↓
POLICY EVALUATION
  ↓
PROPOSED / OWNER REQUIRED
  ↓
OWNER AUTHENTICATION
  ↓
SCOPED APPROVAL
  ↓
APPROVED DECISION
  ↓
SEPARATE EXECUTION GATE
  ↓
AUDIT
```

## Required properties

An approval should be:

- tied to one request;
- attributable to the authenticated owner identity;
- scoped to a declared purpose;
- time-bounded when appropriate;
- amount-bounded for financial actions;
- auditable;
- impossible to silently broaden into another action.

## Future control plane

The web application will call a private API rather than directly manipulating the core. The API will enforce authentication and authorization, while the Governor remains the policy boundary. Execution workers will consume only decisions that have passed the required gates.
