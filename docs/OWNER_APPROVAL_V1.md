# AURELIX Owner Approval V1

Protected actions require an explicit approval object rather than a boolean flag buried in agent state.

## Approval lifecycle

```text
REQUEST
  ↓
PENDING
  ├── APPROVED → eligible for the next execution gates
  ├── REJECTED → blocked
  ├── EXPIRED → blocked
  └── REVOKED → blocked
```

Each approval request has:

- a unique request ID;
- subject/task ID;
- requested action;
- requester identity;
- creation timestamp;
- expiration timestamp.

Each decision records:

- request ID;
- approver identity;
- decision status;
- decision timestamp;
- reason.

## Security properties

An approval is usable only when it matches the exact request, is approved, and has not expired. Approval is not transferable between requests.

The approval layer does not itself authorize arbitrary execution. Resource scope, policy, risk, budget, circuit breaker, execution, verification, and audit gates remain separate.

## Production extensions

Before financial or production use, add authenticated owner identity, durable approval storage, revocation, authorization for who may approve each action class, anti-replay controls, immutable audit correlation, and UI confirmation showing the exact action, amount, target, risk, and expiry before approval.
