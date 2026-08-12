# AURELIX Operations Baseline V1

This document defines the minimum production boundary for AURELIX.

## Runtime states

- BOOTING
- READY
- RUNNING
- DEGRADED
- STOPPING
- STOPPED
- FAILED

## Non-negotiable controls

1. External research content is untrusted data, never privileged instructions.
2. Agents receive only task-specific tools and data.
3. Financial, security, permission, infrastructure and irreversible actions require an approval policy.
4. Business execution is disabled by default until the owner explicitly enables the corresponding policy.
5. Every job has an identity, scope, deadline and audit record.
6. Workers must be restartable and idempotent where practical.
7. Runaway execution is bounded by step, time, retry and cost budgets.
8. Production credentials are never placed in model prompts or long-term knowledge.
9. Memory writes require validation and provenance.
10. Changes to governance/security policy are not self-authorized by agents.

## Required operational layers

```text
CONTROL PLANE
  Governor / Policy / Approval / Audit

RUNTIME PLANE
  Scheduler / Queue / Workers / Execution Plane

INTELLIGENCE PLANE
  Research / Evidence / Academy / Knowledge

INNOVATION PLANE
  Innovation / Experiment / Evaluation / Opportunity

BUSINESS PLANE
  Business / Revenue / Treasury

OBSERVABILITY
  Health / Metrics / Logs / Alerts / Recovery
```

## Production gate

AURELIX is not considered production-ready until automated tests cover authorization bypass, prompt injection through retrieved content, memory poisoning, unauthorized tool invocation, runaway retries/cost, approval bypass, secret leakage, worker restart/recovery and audit integrity.

## Owner authority

The owner can approve or reject high-impact actions. Approval is a separate authorization event; the agent's confidence, reasoning or recommendation cannot substitute for it.
