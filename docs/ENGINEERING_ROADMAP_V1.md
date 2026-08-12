# AURELIX Engineering Roadmap V1

## Phase 0 — Foundation

- Constitution
- Threat model
- Identity and access model
- Decision gates
- Audit model
- Repository hygiene
- Continuous integration

## Phase 1 — Core Control Plane

- Typed domain contracts
- Policy engine
- Governor state machine
- Owner approval lifecycle
- Durable audit events
- Idempotency and correlation IDs
- Structured error model

## Phase 2 — Private API

- API application
- Authentication integration boundary
- Authorization middleware
- Request validation
- Rate limiting
- Secure configuration
- API contract tests

## Phase 3 — Owner Control Center

- Secure login
- System overview
- Pending decisions
- Approval detail view
- Treasury requests
- Opportunities
- Agent status
- Audit explorer
- Security status

## Phase 4 — Engines

- Research
- Academy
- Opportunity
- Innovation
- Build
- Business
- Revenue
- Learning

## Phase 5 — Agents and Workers

- Agent registry
- Capability registry
- Task queue
- Worker lifecycle
- Tool permissions
- Sandboxed execution
- Retry and timeout policies

## Phase 6 — 24/7 Operations

- Scheduler
- Event processing
- Health checks
- Observability
- Alerting
- Backups
- Disaster recovery
- Cost controls

## Phase 7 — Controlled External Integrations

Integrations are introduced one at a time, with a dedicated capability definition, credentials boundary, risk assessment, rate limits, and tests.

## Phase 8 — Revenue Engine

- Opportunity scoring
- Experiment tracking
- Product/service lifecycle
- Customer and sales workflows
- Revenue attribution
- ROI measurement

## Phase 9 — Scale

- Human team identities
- Delegated roles
- Multiple business units
- Mobile client
- Additional execution environments
- Stronger isolation where justified

## Non-Negotiable Engineering Rules

- No secrets in Git.
- No production credentials in model context.
- No unrestricted agent shell access.
- No privileged action based solely on model output.
- No financial execution without the applicable approval gate.
- No critical self-modification directly into production.
- No bypass of the Governor from the UI.
- Security and audit requirements are part of the definition of done.

## Definition of Done

A feature is not complete merely because it works on the happy path. It must have appropriate tests, authorization behavior, failure handling, audit behavior, documentation, and rollback considerations for its risk class.
