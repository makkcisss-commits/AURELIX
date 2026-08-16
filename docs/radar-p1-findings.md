# Master Radar V2 — P1 findings

## P1-RESUME-001 — Mission/execution identity is not integrated in `main`

`AutonomyFabric.run_claimed()` currently creates a new `EconomicMission` during each execution. The resulting `mission_id` is therefore generated in the execution path instead of being the durable business identity supplied by Runtime state. `AdaptiveLoop` also indexes its coordination record by `execution_id`.

The existing runtime recovery invariant document explicitly says retries reuse the same job/execution identifier. That contradicts the required contract where `mission_id` is stable and each new attempt has a distinct `execution_id`.

## P1-RESUME-002 — Resume implementation exists only in an unmerged PR

PR #52/#63 contain a candidate implementation that persists mission context and creates a fresh resume execution id. It must not be merged mechanically because its tests include reference-model tests that do not execute the production resume path, and the implementation needs validation against the current `main` architecture.

## P1-RESUME-003 — Real concurrency proof was missing

The current `main` test suite does not contain an integration test that invokes the production resume operation concurrently from two workers. A new regression test now exercises the durable SQLite claim primitive and proves one claim wins and one loses. This is a partial proof only; the final test must call `AutonomyFabric.resume_mission()` itself.

## P1-RESUME-004 — Restart durability of capability validation is incomplete

`ContinuousIntelligence` is explicitly an in-memory V1 registry. A runtime restart loses its objective/evidence/evaluation/capability state. Resume therefore cannot currently prove that a previously validated capability remains valid after restart. The safe behavior is to fail closed, but the required durable learning/resume contract remains incomplete.
