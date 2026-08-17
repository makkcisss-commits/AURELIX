# AURELIX — Master Engineering Protocol Execution — 2026-08-17

## Source of truth

This execution applies the uploaded **AURELIX Master Engineering Execution Protocol**. Its governing rule is that a capability is not considered functional merely because code, tests, issues, PRs, mocks or documentation exist; the real execution path must be demonstrated.

## Corrections applied

### 1. Canonical authority

The composition root previously instantiated both the runtime Academy and a separate curated Academy. The curated Academy was not used as a mere adapter: it owned independent knowledge state. The canonical composition now keeps one core Academy authority and uses the runtime Academy strictly as the execution adapter for the research-to-learning stage.

### 2. Durable Academy state

Canonical Academy knowledge is now persisted through the existing RuntimeStore and reconstructed after process restart. Validation covers create -> persist -> restart -> restore.

### 3. Durable verified economics

Economic attribution is now persisted through RuntimeStore. The ledger rejects unverified observations, requires a Governor decision and external reference, and is idempotent on the external reference. Validation covers duplicate delivery and restart restoration.

### 4. Mission identity versus execution identity

`mission_id` is now carried in the durable job payload and is independent from `execution_id`. A retry/resume therefore creates a new execution attempt without silently creating a new business mission.

### 5. Atomic resume

A durable `MissionResumeCoordinator` creates a mission-state table and atomically reserves the next execution attempt. Concurrent resume requests converge on one queued attempt. The reservation and job creation occur in one SQLite transaction.

### 6. Fail-closed restart behavior

Resume requires validated capability state. If the in-memory validation evidence is unavailable after restart, resume is refused rather than inferred from the persisted mission record.

### 7. Repository-integrity cleanup

Temporary audit-marker artifacts that were deliberately present in the repository were removed. They were causing the repository-integrity CI gate to fail before the real test suite could execute.

## Verification added

- `tests/test_master_protocol_durability.py`
- `tests/test_mission_resume_durability.py`

These tests exercise restart persistence, external-reference idempotency and concurrent resume convergence.

## Current CI truth

The first CI attempt on this branch failed at repository-integrity validation because of the marker artifacts. Those artifacts have now been removed and a new CI run has been queued on the corrected commit. No claim of passing CI is made until the new run completes.

The new run includes Python 3.11/3.12 tests, PostgreSQL integration, production configuration validation, container build/readiness and security checks, plus system regression.

## External blockers

The protocol requires a real financial provider before production financial execution can be claimed. A code path cannot manufacture that dependency. Until a real provider is connected and its live path is demonstrated, financial execution remains externally blocked.

Likewise, repository branch protection is a GitHub administration control rather than an application-code correction. It must be enabled and verified at the repository level before the repository can claim protected-main governance.

## Kitsu-oriented execution discipline

Kitsu's documented production model emphasizes explicit workflows, task/status tracking, milestones, assignments and production reports. AURELIX's protocol is therefore tracked as execution states rather than optimistic completion labels: **MISSING / BLOCKED / IMPLEMENTED / INTEGRATED / VALIDATED / FAILED / RECOVERY_REQUIRED**. This is consistent with the protocol's own strict-status rule and prevents a dashboard from becoming a false-success surface.
