# AURELIX Execution Plane V1

The Execution Plane is the security boundary between an autonomous planner/orchestrator and executable engine handlers.

## Invariants

- Every execution has an explicit `agent_id`.
- Every execution has a task-scoped allowlist of engines.
- Unregistered engines fail closed.
- An agent cannot execute an engine outside its scope.
- Execution is bounded by a runtime limit.
- The execution environment is explicit and defaults to `sandbox`.
- The receipt records identity, engine, environment, status, elapsed time, and output.

```text
UNTRUSTED MODEL PLAN
        |
        v
  EXECUTION PLANE
   /     |      \
identity scope  limits
        |
   policy check
        |
   +----+----+
   |         |
 ALLOW     DENY
   |         |
   v         X
 ENGINE
   |
 RECEIPT
   |
 AUDIT
```

The plane intentionally does not let a model grant itself permissions. Production, capital, security-policy changes, and other high-impact actions should use separate approval gates rather than being unlocked by a broader agent scope.

## Current limitation

The runtime limit is an elapsed-time check after handler execution. It is not an OS-level hard kill. Production workers should run handlers in isolated processes/containers with external timeouts and resource quotas.
