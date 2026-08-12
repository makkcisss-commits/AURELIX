# AURELIX Worker Supervisor V1

The Worker Supervisor is the first operational watchdog for the execution plane.

## Responsibilities

- register workers with explicit policy;
- track `STARTING`, `RUNNING`, `DEGRADED`, `STOPPED`, and circuit `OPEN` states;
- accept heartbeats;
- detect stale workers;
- count failures and bounded retries;
- open a circuit after repeated failures;
- allow a cooldown before recovery;
- reset failure/retry state after successful work.

## Safety boundary

This component does **not** execute arbitrary code, grant permissions, manage credentials, or replace process/container isolation. A production deployment should put workers behind an OS/container boundary and enforce CPU, memory, filesystem, network, and wall-clock limits outside the model.

## Failure behavior

```text
RUNNING
  │
  ├─ heartbeat timeout ──> DEGRADED
  │
  ├─ transient failure ──> DEGRADED ──> bounded retry
  │
  └─ repeated failures ──> OPEN
                              │
                              ▼
                           cooldown
                              │
                              ▼
                          DEGRADED
```

The supervisor fails closed: an unknown worker cannot be started or heartbeated, and an open circuit cannot be started until its cooldown has elapsed.

This complements the existing Governor, Agent Identity, Approval, Execution Plane, Health, Persistence, and Audit layers. OWASP's current agent guidance recommends least privilege, monitoring, circuit breakers, bounded retries/tool chains, and explicit controls for high-impact actions. NIST's 2026 agent identity work also highlights identification, authorization, auditing, non-repudiation, and prompt-injection mitigation as core concerns.
