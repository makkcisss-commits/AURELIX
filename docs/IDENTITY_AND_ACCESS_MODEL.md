# AURELIX Identity & Access Model

## Objective

Define a secure identity and authorization boundary for the private AURELIX control plane.

## Roles

| Role | Purpose | Default privilege |
|---|---|---|
| OWNER | Ultimate human authority | Protected actions + administration |
| ADMIN | Trusted human operator | Explicitly delegated administration |
| OPERATOR | Day-to-day human operations | Scoped operational actions |
| AGENT | Machine worker | Task-scoped permissions |
| AUDITOR | Read-only oversight | Audit and evidence access |
| SERVICE | Internal software identity | Endpoint-scoped machine access |

No role grants permissions merely because an identity has been authenticated.

## Authorization Layers

```text
Authentication
    ↓
Identity
    ↓
Role
    ↓
Resource
    ↓
Action
    ↓
Policy
    ↓
Context / Risk
    ↓
Allow / Deny / Owner Approval
```

## Owner

The initial owner is defined in `docs/OWNER_IDENTITY.md`. The production identity provider, authentication factor(s), and account identifier are configured outside source code.

## Protected Actions

Protected actions include, at minimum:

- material financial transactions;
- privilege elevation;
- security-policy changes;
- identity-provider changes;
- production deployment of protected components;
- disabling mandatory audit controls;
- changing ownership or governance configuration.

These actions must reach an explicit authorization gate. Authentication alone is never sufficient.

## Least Privilege

Every agent and service must have a declared capability set. Permissions should be narrow, time-bounded where practical, and revocable.

## No Shared Privileged Accounts

The owner account is personal and must not be shared. Each future human collaborator receives an individual identity and an auditable role assignment.

## Emergency Access

Emergency controls will be implemented separately from ordinary permissions. Emergency access must be explicitly invoked, narrowly scoped, time-limited, and audited.

## Audit Requirements

Authorization decisions must record enough context to reconstruct:

- actor identity;
- role;
- requested action;
- resource;
- policy decision;
- approval requirement;
- approval identity where applicable;
- timestamp;
- outcome;
- correlation/request ID.

## Future Web Control Plane

The web application will never be treated as a direct privileged shell. It will authenticate the user and call the private AURELIX API. The API and Governor remain responsible for authorization and protected-action gates.
