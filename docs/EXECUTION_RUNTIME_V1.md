# AURELIX Execution Runtime V1

The Execution Runtime is the first deterministic boundary between an approved request and an executable operation.

```text
Execution Request
       ↓
Circuit Breaker
       ↓
Resource Scope
       ↓
Future: Policy / Risk / Approval / Budget Gates
       ↓
Bounded Operation
       ↓
Success → reset health state
Failure → record failure → possible OPEN circuit
```

## Current Boundary

V1 deliberately accepts a Python callable supplied by trusted application code. It does not execute arbitrary shell commands, URLs, plugins, or model-generated code.

This restriction is intentional. External tools will be introduced through explicit adapters with their own identity, permissions, budgets, timeouts, validation, and audit events.

## Fail-Safe Behavior

- An open circuit blocks execution.
- An out-of-scope request is denied before the operation is called.
- An operation exception counts as a runtime failure.
- The runtime does not silently retry failed operations.
- Authorization is deterministic and independent of model output.

## Next Integration

Before production execution, this boundary must be integrated with:

1. Governor policy decisions;
2. owner approval for protected actions;
3. execution budgets and timeouts;
4. immutable audit events;
5. authenticated service identities;
6. explicit tool adapters;
7. rollback or compensation strategies where applicable;
8. integration and security tests.
