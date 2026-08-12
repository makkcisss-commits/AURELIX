# AURELIX Execution Gate V1

The Execution Gate is the final fail-closed decision boundary before any future side effect.

It requires all five conditions:

1. explicit scoped owner approval;
2. policy permission;
3. budget permission;
4. circuit breaker readiness;
5. audit readiness.

If any condition is false, the result is `BLOCKED`.

```text
Proposal
  ↓
Governor / Owner Approval
  ↓
Policy
  ↓
Budget
  ↓
Circuit Breaker
  ↓
Audit Ready
  ↓
EXECUTION GATE
  ├── BLOCKED
  └── READY
```

`READY` is an authorization state only. This module performs no payment, network request, shell command, deployment, or other external side effect.

A future executor must accept only a gate-approved execution token/context and must re-check the relevant authorization immediately before the side effect. The executor will be a separate trust boundary.
