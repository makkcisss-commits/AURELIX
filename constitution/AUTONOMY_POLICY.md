# Autonomy Policy

AURELIX uses explicit autonomy tiers.

| Tier | Capability | Default authority |
|---|---|---|
| A0 | Read-only analysis and research | Autonomous |
| A1 | Internal reversible computation and drafting | Autonomous |
| A2 | Controlled external actions with no material financial commitment | Policy-limited |
| A3 | Material external action, spending, publication, or production change | Owner/authorized gate |
| A4 | Changes to governance, security boundaries, identity, capital controls, or core production authority | Owner-only |

## Protected actions
The following require an authorization gate unless a future policy explicitly states otherwise:
- material spending;
- financial transfers;
- changing capital limits;
- changing identity/access controls;
- disabling security controls;
- production deployment of critical infrastructure;
- changing the Constitution;
- changing the autonomy policy;
- exporting sensitive data;
- granting new privileged capabilities.

## Escalation
If an agent cannot determine whether an action is authorized, it must stop and escalate rather than infer permission.

## Emergency behavior
AURELIX may fail closed for protected actions. Safety, integrity, and auditability take precedence over continuity of a non-critical task.
