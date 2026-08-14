# System Integration Audit V1

## Scope

Audit AURELIX as one machine: orchestration, runtime, scheduler, Governor, autonomy, learning, provenance, recovery, and service lifecycle.

## Findings

### Critical: execution submission has a lower-level bypass

`AurelixSystem.submit()` delegates directly to `AurelixRuntime.submit()`. `AurelixRuntime.submit()` only checks that a handler is registered and enqueues the job; it does not require a Governor authorization decision. The higher-level `Orchestrator.submit()` does route through Governor, but the unified system exposes a separate submission path.

This means the architecture currently has two authorization paths:

1. Orchestrator → Governor → Runtime
2. AurelixSystem → Runtime

The second path can bypass the policy boundary for registered capabilities. This conflicts with the intended invariant that Governor is the single execution authorization boundary.

Evidence: `src/aurelix_runtime/orchestrator.py`, `src/aurelix_runtime/system.py`, `src/aurelix_runtime/runtime.py`.

### High: legacy long-running service remains separate

`src/aurelix_runtime/service.py` defines a second `RuntimeService` lifecycle around `PersistentJobQueue` and `SupervisedWorker`, while `AurelixSystem`/`AurelixRuntime` define the canonical durable system lifecycle. The repository currently retains both abstractions and tests for the legacy service.

This increases the risk of two competing execution fabrics and makes it harder to prove that production always uses the canonical path.

### High: autonomous cycle needs end-to-end proof

The repository has strong component and composition tests, but the next validation must prove a complete unattended cycle from scheduled work through orchestration, governed execution boundary, durable result, verified economic learning, provenance, and subsequent scheduling, including restart/recovery.

## Required remediation

- Make the Governor authorization boundary unavoidable for externally submitted executable work.
- Define an explicit internal-only mechanism for trusted runtime/system plumbing so internal scheduling cannot become a policy bypass.
- Consolidate or explicitly quarantine the legacy `RuntimeService` path.
- Add a system-level adversarial test proving that direct runtime submission cannot bypass policy.
- Add a full unattended multi-cycle integration test including restart and recovery.
- Preserve audit/provenance across every transition.
