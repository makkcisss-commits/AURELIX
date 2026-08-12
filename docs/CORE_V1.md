# AURELIX Core V1

## Goal

V1 establishes a deterministic governance boundary before external integrations, autonomous workers, financial tooling, or production deployment are connected.

## Request lifecycle

```text
Actor
  ↓
DecisionRequest
  ↓
Governor
  ↓
PolicyEngine
  ├── approved → caller may continue within scope
  └── protected/rejected → stop or request authorization
  ↓
AuditEvent
```

## Design constraints

- Policy evaluation is deterministic and testable.
- The Governor cannot grant authority that policy does not define.
- Protected actions fail closed.
- The audit boundary is created at decision time, not after execution.
- The current audit sink is in-memory for testing; production requires durable append-only storage.
- No external credentials or secrets belong in source control.

## Next core milestones

1. Typed owner-approval records with expiration and scope.
2. Durable append-only audit storage.
3. Identity and role model.
4. Task and workflow state machine.
5. Event bus and idempotency keys.
6. Treasury request/approval domain.
7. Sandbox execution boundary.
8. API boundary for the private control center.
9. Authentication and session security.
10. Integration tests and threat-model review.
