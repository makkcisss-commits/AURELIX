# AURELIX Persistence & Recovery V1

AURELIX uses SQLite as the initial durable runtime state layer. The execution identifier (`job_id`) is stable across retries and is the idempotency key for one execution.

## Execution invariants

- Every execution has a unique durable execution ID.
- `queued → running` is claimed atomically; two workers cannot claim the same execution.
- `running → completed` is committed together with the durable result.
- A completed result cannot be overwritten by a later retry.
- A failed execution cannot transition to success.
- Retries reuse the same execution ID and therefore cannot create a second execution record.
- `RUNNING` rows carry worker and heartbeat metadata so abandoned work can be detected.
- Recovery records the interruption, then either requeues the same execution or terminally fails it when the attempt budget is exhausted.
- Recovery is idempotent because only rows currently in `running` can be recovered.
- Audit events record interruption and failure outcomes independently of application logs.

## Recovery model

```text
PENDING / QUEUED
      │ claim
      ▼
   RUNNING ────────────── crash / stale heartbeat
      │                         │
      │ result + transition     ▼
      │                      INTERRUPTED
      ▼                         │
  COMPLETED                     ├── retry budget → QUEUED
                                └── exhausted → FAILED
```

The implementation deliberately uses atomic state transitions and idempotency rather than enabling `SERIALIZABLE` globally. Stronger isolation can be introduced for a specific invariant if measurement shows it is necessary.

## Runtime boundary

`RuntimeStore` is the source of truth for execution lifecycle. The worker-facing queue is an adapter over that store; the in-memory `EngineStore` is only used for engine-level state and audit compatibility. This prevents the runtime scheduler from silently losing execution state when the process restarts.

## SQLite / PostgreSQL boundary

SQLite is the runtime persistence implementation for the initial single-node deployment. PostgreSQL remains a separate knowledge/integration target rather than an implicit runtime dependency. If AURELIX moves to PostgreSQL for multi-worker production, the same execution contract must be preserved: unique execution identity, conditional claims, atomic terminal results, explicit conflict handling, leases/heartbeats, and recovery tests.

## Production hardening

Before the runtime becomes business-critical, add tested backup/restore, retention policies, migration tooling, encryption-at-rest decisions, operational metrics, and a documented failover procedure. These are deployment hardening requirements, not substitutes for the execution invariants above.
