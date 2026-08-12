# AURELIX Audit Architecture V1

Audit is a control, not merely a log. Protected decisions and executions must leave an evidence trail that can be inspected after the fact.

## Current layers

```text
Core AuditEvent
      ↓
AuditLog (in-memory test sink)
      ↓
AuditStore (append-only JSONL foundation)
      ↓
Future protected production backend
```

## Required event context

Events should identify, where applicable:

- actor;
- subject/request;
- action/outcome;
- timestamp;
- correlation/request ID;
- policy decision;
- authorization/approval context;
- resource scope;
- budget/limit context;
- error or verification result.

## Production Requirements

The JSONL store is intentionally a local foundation and must not be treated as the final production security control. A production backend should provide:

- append-only semantics;
- authenticated and authorized writers;
- restricted readers;
- integrity/tamper detection;
- durable storage;
- backup and recovery;
- retention policy;
- time synchronization strategy;
- monitoring and alerting.

## Fail-Safe Principle

If a policy requires an audit event and the required audit sink is unavailable, the protected operation should fail closed. The runtime must never silently execute a protected action merely because logging failed.
