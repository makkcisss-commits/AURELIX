# AURELIX Autonomy Policy

AURELIX uses bounded autonomy. Capability is never authority by itself.

| Level | Meaning | Examples |
|---|---|---|
| A0 | Observe | read state, inspect telemetry |
| A1 | Recommend | research, analysis, proposals |
| A2 | Reversible execution | isolated builds, local experiments, non-critical transformations |
| A3 | Bounded operations | approved operational workflows within explicit limits |
| A4 | Protected | financial, security, governance, critical deployment |

## Rules

1. An actor may not perform an action above its assigned level.
2. A4 actions require an explicit owner authorization path.
3. Production deployment is protected even when an agent created the change.
4. Autonomy increases only after evidence, tests, and a policy change.
5. Emergency controls must fail closed rather than silently expand authority.
6. Every protected decision must be auditable.
7. If an actor cannot determine whether an action is authorized, it must stop and escalate rather than infer permission.

## Protected actions

Unless a future, explicitly approved policy says otherwise, these require an owner authorization gate:

- material spending or financial transfers;
- changing capital limits;
- changing identity or access controls;
- disabling security controls;
- critical production deployment;
- changing the Constitution or autonomy policy;
- exporting sensitive data;
- granting privileged capabilities.

## Future implementation

The policy engine will evolve toward declarative policy documents, signed approvals, scoped credentials, time limits, spend limits, environment-specific permissions, and durable audit storage. Until those controls exist, AURELIX remains intentionally conservative.
