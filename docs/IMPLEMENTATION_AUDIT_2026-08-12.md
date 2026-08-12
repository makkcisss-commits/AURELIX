# AURELIX implementation audit — 2026-08-12

## Verified in source

- Python package layout and pytest configuration are present.
- Durable SQLite runtime store exists for jobs, audit, approvals and heartbeat.
- Runtime now recovers interrupted jobs and applies a bounded retry budget.
- Runtime can register and execute the governed Research→Business pipeline.
- Provenance lineage traverses parent subjects correctly.
- Governance checks provenance, actor identity, policy and records transitions.
- A configurable HTTPS research-provider adapter is wired through `AURELIX_RESEARCH_URL`.
- The supervised-worker compatibility path now constructs a valid pipeline runner.
- The private web API contract is read-only and authenticated; deployment documentation requires HTTPS termination at a trusted edge.
- Browser API routing matches the documented `/v1/control/snapshot` contract.
- CI configuration runs the Python test suite with pytest.

## Important boundaries

The repository is not a deployed production system. The external identity provider, secret manager, HTTPS ingress, real research provider credentials, production database operations, and operational monitoring remain deployment responsibilities.

The default research engine remains safe/degraded when no research provider is configured: it does not invent evidence. Business execution remains approval-gated and proposal-oriented.

## Security check

The Git repository is currently public. Proprietary implementation and real credentials must not be stored here until repository visibility is changed to private. The available GitHub integration used for this audit does not expose a repository-visibility mutation, so that change must be performed in GitHub settings by an administrator.

## Test evidence

New regression coverage was added for:

- runtime pipeline execution;
- retry budget and terminal failure;
- HTTPS research-provider validation;
- provenance lineage;
- supervised worker execution;
- existing pipeline/governance behavior.

The connected GitHub Actions workflow is configured to run `pytest -q`, but no workflow run/status was available for the latest commits during this audit. The code was therefore inspected and regression tests were added, but a remote CI pass is not claimed.
