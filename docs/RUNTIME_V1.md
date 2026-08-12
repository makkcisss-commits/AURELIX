# AURELIX Runtime V1

AURELIX now has a durable orchestration kernel for continuous operation.

## Components

```text
Scheduler
   ↓
Durable Job Queue (SQLite)
   ↓
Worker / Handler Registry
   ↓
Audit Trail
   ↓
Knowledge / Research / Academy / Business handlers
```

## Properties

- durable local state across process restarts
- explicit job registration (unknown work cannot be submitted)
- isolated worker failures (one failed job does not terminate the runtime loop)
- heartbeat and health state
- recurring scheduler
- authenticated read-only runtime endpoint
- no payment, deployment, security-policy, or governance mutation endpoint

## Production boundary

The bundled HTTP server binds to loopback by default and requires `AURELIX_CONTROL_TOKEN`. HTTPS should be provided by a hardened reverse proxy or service mesh; the application server must not be exposed directly to the public Internet.

Before production, configure a real identity provider, TLS, secret manager, network policy, structured logs, metrics/tracing, backup/restore, and external alerting.

## Autonomous operating model

AURELIX can autonomously execute registered low-risk research/maintenance jobs, preserve results, learn from experiments, and prepare proposals. High-impact actions remain gated by policy and owner approval.
