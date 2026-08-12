# AURELIX Resource Scope Model

AURELIX authorization is not satisfied by role membership alone. A machine or human identity must also be authorized for the specific resource, operation, and target scope.

```text
Identity
  ↓
Role
  ↓
Resource
  ↓
Operation
  ↓
Target Scope
  ↓
Policy / Risk Gate
```

## Example

A Research Agent may be permitted to read research records for `project-alpha` without receiving permission to read Treasury records or production secrets.

```text
research-agent
  research:read
  scope=project-alpha
```

This does not imply:

```text
research-agent
  treasury:read
  secrets:read
  production:write
```

## Fail Closed

Missing, mismatched, expired, or ambiguous scope must deny the operation. The system must not widen scope automatically to make an operation succeed.

## Wildcard Scope

A wildcard scope is an explicit high-privilege capability and must not be used for ordinary agents. It should be reserved for tightly controlled administrative cases and subject to additional policy.

## Future Extensions

The initial implementation is intentionally small. Future versions should add:

- time-bounded permissions;
- tenant/project/resource hierarchies;
- deny rules;
- policy versioning;
- risk classification;
- owner approval integration;
- capability tokens;
- revocation;
- immutable audit correlation;
- service-to-service authentication.

The scope layer must remain deterministic and testable. An LLM must never be the final authority on whether a permission exists.
