# AURELIX Persistence & Recovery V1

AURELIX now has a durable SQLite state layer for runtime jobs.

## Guarantees

- Jobs are persisted before execution.
- Running jobs are recoverable after an unclean process restart.
- Results are persisted separately from job state.
- Audit events are persisted with UTC timestamps.
- SQLite WAL mode is enabled for better concurrent read behavior.

## Recovery model

```text
PROCESS CRASH
     ↓
DATABASE REMAINS
     ↓
STARTUP
     ↓
RECOVER RUNNING JOBS
     ↓
QUEUE
     ↓
WORKER
```

## Security boundary

Persistence does not grant authority. A stored job still has to pass the Runtime's identity, capability and policy controls before execution. External research content is data, not executable instruction.

## Production hardening still required

SQLite is appropriate for the initial single-node runtime and development deployment. A production multi-worker installation should add backup/restore procedures, encryption at rest where appropriate, database migrations, retention policies, connection management, and a tested failover strategy before becoming business-critical.
