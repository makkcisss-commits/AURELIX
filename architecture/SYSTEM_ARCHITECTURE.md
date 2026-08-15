# AURELIX Architecture

AURELIX is one governed enterprise machine with specialized engines behind one canonical composition root.

```text
Owner / CEO
    ↓
Identity / Authorization
    ↓
Governor + Policies + Audit
    ↓
SystemOrchestrator
    ↓
EngineFactory  ← canonical composition root
    ├── Research / Evidence / Knowledge / Academy
    ├── Innovation / Experiment / Evaluation
    ├── Opportunity / Business / Revenue / Treasury
    ├── Learning / Economic Feedback
    └── AutonomyFabric
            ↓
      Shared Runtime + Scheduler + MessageFabric + durable state
            ↑
      SystemIntegrityController
            ↑
  SystemDiagnostics + SystemValidation
```

## Canonical flow

```text
Research
  → source-backed evidence
  → knowledge
  → opportunity candidates
  → economic qualification
  → Governor decision
  → owner approval when required
  → bounded execution
  → real observation
  → revenue measurement
  → verified learning
  → next-cycle context
```

## Composition rule

`EngineFactory` owns the production composition. `AurelixSystem` is a façade over that composition. `SystemOrchestrator` must call the factory's canonical cycle rather than constructing a parallel path. `AutonomyFabric` shares the exact engine instances and durable store used by `EnterpriseLoop`.

## Integrity control plane

`SystemIntegrityController` is an additive, read-only control plane. It does not become a second orchestrator and it does not silently repair critical state. It continuously verifies:

- one live owner per protected responsibility;
- shared engine identity across `EngineFactory`, `EnterpriseLoop` and `AutonomyFabric`;
- one runtime execution authority per job kind;
- unique scheduler identities;
- valid durable mission-resume state and lease metadata;
- explicit failures for legacy/ambiguous state instead of unsafe guesses.

A replacement implementation must be wired through the canonical composition root. The old implementation must not remain a second live authority for the same responsibility. Safe migrations are explicit and auditable; critical changes remain behind the existing approval/change-management boundary.

## Authority rule

Recommendation, model output, research content, opportunity score and economic forecast are never authorization. The Governor and applicable owner approval are the authority boundary. Runtime only executes work that has passed the required gate.

## Economic rule

The system ranks opportunities using evidence, expected value, effort, risk, confidence, complexity and time-to-result. It must then verify demand, monetization path and source reality before revenue admission. Forecasts remain forecasts until an external or otherwise authentic observation is recorded.

## Reliability rule

Jobs are durable, bounded, retryable and lease-fenced. Messages are structured and idempotent. Recovery must preserve audit and provenance. Mission identity (`mission_id`) remains stable while execution identity (`execution_id`) identifies each attempt.

## Integrity rule

There is one canonical source per responsibility. Exact duplicate file content is an integrity failure and is checked by CI. Historical documents may remain for traceability, but they are not alternate authorities. The integrity control plane turns this architectural rule into a machine-readable readiness verdict.

## Production boundary

External identity, secret management, payment providers, real research providers, network ingress, monitoring and production data remain deployment concerns. The repository provides the governed skeleton and integration contracts; it must never fabricate real business results.
