# Runtime recovery invariants

AURELIX runtime execution state is durable and must remain correct across crashes and retries.

## Required invariants

1. A job can transition from `queued` to `running`, then to `completed` or `failed`.
2. A stale `running` job is recovered without being treated as successful.
3. `mission_id` is the durable business identity and remains stable across retries and resume operations.
4. `execution_id` identifies one concrete execution attempt. A new retry/resume attempt must receive a new execution identifier.
5. A successful terminal state is committed atomically with its durable result.
6. A failed terminal state records a durable failure result.
7. A terminal execution cannot be completed again with a different result.
8. Concurrent workers may not claim the same queued execution or the same mission-resume reservation.
9. Runtime state is stored on a persistent Docker named volume in the production Compose deployment.
10. Resume coordination is lease-fenced. An expired reservation may be replaced; an active reservation must reject a concurrent claimant.
11. If capability-validation state required for a resume is unavailable after restart, the system must fail closed with an explicit recovery/unavailable state rather than infer validation.

## Current implementation status

The current `main` branch does **not yet prove all of these invariants**. In particular, the Runtime retry implementation still reuses the same job identifier, `AutonomyFabric` creates its `EconomicMission` inside an execution, and `ContinuousIntelligence` is an in-memory V1 registry. These gaps are tracked as P1 work and must be resolved before the runtime can claim full mission/execution durability.

These invariants are intentionally stronger than process-local state: restarting the process or recreating the container must not invent success or silently duplicate execution.
