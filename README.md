# AURELIX

**Autonomous Unified Research, Evolution, Learning & Intelligence eXecutive**

AURELIX is a private entrepreneurial intelligence system designed to research, learn, discover opportunities, build products and services, operate authorized business workflows, measure results, and continuously improve under human capital governance.

> **One intelligence. Many engines. One enterprise. One owner. Continuous learning. Bounded autonomy.**

## Current status

AURELIX is in **foundation / core engineering**. The current implementation prioritizes governance, authorization, auditability, security, and testable decision logic before adding broad autonomous capabilities.

The repository currently includes:

- system constitution and governance policies;
- bounded autonomy model A0–A4;
- capital-control policy;
- owner identity and scoped approval contracts;
- Governor and policy core in Python;
- audit and decision models;
- identity and access model;
- threat model and security baseline;
- private control-plane architecture;
- automated tests and GitHub Actions CI.

## Development / Codespaces

AURELIX is a **Python/FastAPI application with a static browser UI**. It is not a Node.js application and the repository intentionally has no Node dependency tree.

The Codespaces configuration installs the Python dependencies automatically. After creating or rebuilding the Codespace:

```bash
npm run dev
```

`npm run dev` is a small compatibility launcher that starts the Python FastAPI server on port `8000`; it does not install or manage Node packages.

Equivalent direct command:

```bash
PYTHONPATH=src AURELIX_HOST=0.0.0.0 AURELIX_PORT=8000 python -m uvicorn aurelix_core.server:app --reload
```

For the backend package and tests:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest
```

The server serves the `web/` control-center UI at `/` and exposes health/readiness endpoints at `/health` and `/ready`.

## Architecture

```text
Owner / CEO
     |
     v
  Identity
     |
     v
Authorization
     |
     v
  Governor
     |
     +-------------------------------+
     |                               |
     v                               v
Engines                         Control Plane
     |                               |
     v                               v
Agents / Workers                Private API
     |                               |
     +---------------+---------------+
                     |
                  Audit
                     |
                  Treasury
                     |
              Protected execution
```

### Intelligence engines

- Research
- Academy
- Opportunity
- Innovation
- Build
- Business
- Revenue
- Learning

### Governance boundary

AURELIX may research, analyze, recommend, test, build, and execute authorized work. It does not own the company's capital or redefine its own authority.

Material financial, security, governance, privileged-access, and critical production actions require the applicable authorization gate.

## Security model

AURELIX follows a resource-centric, least-privilege model. Being private or difficult to discover is not considered a security control. The future web control plane will sit behind strong authentication, authorization, HTTPS, rate limiting, secure sessions, validation, monitoring, and an explicit Governor boundary.

External content and model output are treated as potentially untrusted. No prompt, document, web page, or tool output can grant itself authority.

See:

- `constitution/SYSTEM_CONSTITUTION.md`
- `constitution/AUTONOMY_POLICY.md`
- `constitution/CAPITAL_CONTROL_POLICY.md`
- `constitution/SECURITY_POLICY.md`
- `docs/IDENTITY_AND_ACCESS_MODEL.md`
- `docs/OWNER_AUTHORIZATION.md`
- `docs/THREAT_MODEL.md`
- `docs/SECURITY_BASELINE_V1.md`
- `docs/CONTROL_PLANE_ARCHITECTURE.md`

## Owner

The initial Owner / CEO is **Makan Sissoko**. Authentication credentials are never stored in source code. The production identity provider and secret-management layer will remain outside the domain model.

## Development principles

1. Security before convenience.
2. Governance before autonomy.
3. Evidence before escalation.
4. Least privilege by default.
5. Fail closed for protected operations.
6. Sandbox before production.
7. Tests before capability expansion.
8. Audit before scale.
9. Reversible changes where practical.
10. Human control over material capital decisions.

## Roadmap

```text
FOUNDATION
  -> Core contracts
  -> Identity / authorization
  -> Governor
  -> Audit
  -> Security baseline

CONTROL PLANE
  -> Private API
  -> Owner console
  -> Decision center
  -> Treasury center
  -> System health

INTELLIGENCE
  -> Research
  -> Academy
  -> Opportunity
  -> Innovation
  -> Learning

EXECUTION
  -> Build
  -> Business
  -> Revenue
  -> Controlled agents

SCALE
  -> 24/7 workers
  -> Human team
  -> Mobile client
  -> Multiple business engines
```

## Important

The repository must be made **private before proprietary implementation, production configuration, business strategy, or sensitive data is stored here**. Never commit API keys, passwords, payment credentials, private keys, tokens, or production connection strings.
