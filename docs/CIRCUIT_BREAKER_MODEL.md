# AURELIX Circuit Breaker Model

AURELIX uses deterministic circuit breakers as a safety boundary around failure-prone or high-impact execution paths.

## States

```text
CLOSED → normal execution
   │
   │ repeated failures
   ▼
OPEN → execution blocked
   │
   │ explicit recovery policy
   ▼
HALF_OPEN → limited recovery test
   │
   ├── success → CLOSED
   └── failure → OPEN
```

The current core implementation establishes the CLOSED/OPEN foundation. HALF_OPEN recovery policy will be introduced only when the execution runtime has explicit health checks and audit semantics.

## Principles

- A breaker fails closed for the protected operation when it is open.
- Failure thresholds are deterministic and configurable by policy.
- A model must never be able to silently disable a breaker.
- Opening a breaker should produce an auditable system event when integrated with the runtime.
- Recovery must be explicit and observable.
- Circuit breakers complement, rather than replace, authorization, resource scopes, budgets, and human approval.

## Why AURELIX Uses Them

Circuit breakers protect against repeated failures, runaway loops, unstable integrations, and cascading failures. They are one layer of defense; they do not decide whether an action is authorized.
