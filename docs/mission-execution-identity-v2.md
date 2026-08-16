# Mission / execution identity contract v2

AURELIX distinguishes business identity from execution-attempt identity.

## Contract

- `mission_id` is the durable business identity. It remains stable across retries and resume operations.
- `execution_id` identifies one concrete execution attempt. A retry/resume that creates a new attempt must receive a new `execution_id`.
- A blocked mission must persist its mission context before the blocking execution becomes terminal.
- Resume coordination is durable and lease-fenced. At most one resume attempt may be owned at a time.
- A completed resume must be replay-safe: a second resume request returns the already completed result rather than creating another execution.
- A failed/expired resume may be replaced by a new attempt, subject to the same Governor and execution gates.
- Capability learning/validation never grants execution authority by itself.

## Current implementation status

The current `main` branch does not yet satisfy this contract end-to-end. `AutonomyFabric` creates `EconomicMission` inside each execution and `AdaptiveLoop` keys its in-memory mission registry by execution id. The production runtime retry model also reuses the same job id. These facts are tracked as P1 work and must not be described as durable mission/execution separation until the real Runtime path and restart/concurrency tests prove it.
