# AURELIX

Private entrepreneurial intelligence and execution system.

> One intelligence. Many engines. One enterprise. One owner. Continuous learning.

AURELIX is designed to research, learn, discover opportunities, build products and services, operate authorized business activities, measure outcomes, and improve continuously under explicit human governance.

## Founding rule

**Intelligence may propose. Agents may execute authorized work. The Governor may orchestrate. Capital remains under owner control.**

AURELIX is not an uncontrolled self-modifying system. Production-critical changes, material financial actions, privileged access, and other protected operations require the authorization defined by policy.

## Core loop

```text
Research → Academy → Innovation → Opportunity → Build → Business → Revenue → Learning → Research
```

## Repository status

This repository is currently the **foundation layer (V1)**. It establishes the constitution, security boundaries, domain contracts, control-plane skeleton, testing, and CI before autonomous capabilities are enabled.

## Architecture

```text
Owner / CEO
    │
    ▼
Governor / Control Plane
    ├── Research Engine
    ├── Academy Engine
    ├── Opportunity Engine
    ├── Innovation Engine
    ├── Build Engine
    ├── Business Engine
    ├── Revenue Engine
    ├── Learning Engine
    └── Treasury
             │
             ▼
       Audit / Security
```

## Security posture

- Least privilege.
- No secrets in source control.
- Protected production boundary.
- Explicit authorization for material capital actions.
- Auditability for critical decisions.
- Sandboxed experimentation before production.
- Server-side authorization; never trust the client.

The web control surface will be private and authenticated. It will not rely on obscurity as a security control.

## Development principles

1. Build the control plane before autonomous agents.
2. Prefer explicit state machines over hidden agent behavior.
3. Every important action has an owner, policy, status, and audit trail.
4. Experiments are isolated from production.
5. New autonomy is earned through tests and evidence.
6. Financial execution is separated from financial recommendation.

## Initial objective

**ZERO → FIRST REVENUE ENGINE**

The system must start from a minimal-resource assumption and identify realistic, legal, evidence-backed opportunities before expanding its operational surface.

## Roadmap

- [x] Founding repository
- [x] Constitution and governance boundaries
- [x] Control-plane domain model
- [x] Treasury request state machine
- [x] Audit model
- [x] Security baseline
- [x] Minimal API skeleton
- [x] Automated tests and CI
- [ ] Persistent database
- [ ] Authenticated private control web
- [ ] Research connectors
- [ ] Academy knowledge store
- [ ] Opportunity scoring
- [ ] Sandboxed agent runtime
- [ ] Human approval workflows
- [ ] Production deployment
- [ ] Mobile application

## Important

Do not commit API keys, passwords, private tokens, payment credentials, or other secrets. Use environment/secret management instead.
