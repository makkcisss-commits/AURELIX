# AURELIX Control Plane V1

The Control Plane is the composition boundary for AURELIX's deterministic execution safeguards. It coordinates existing gates; it does not create authority.

```text
Decision Request
      ↓
Governor / Policy
      ↓
Owner gate when required
      ↓
Budget guard
      ↓
Resource scope
      ↓
Circuit breaker
      ↓
Execution runtime
      ↓
Audit
```

## Design rule

No model-generated text is treated as permission. The Control Plane consumes typed domain objects and deterministic decisions.

## Current scope

V1 composes the Governor, Budget Guard, Resource Scope, Circuit Breaker, Execution Runtime, and Audit Log. Owner approval remains a separate domain object and must be integrated with authenticated owner identity before protected financial or production actions are enabled.

## Important limitation

The current implementation is a core library boundary, not a network-facing API. It must not be exposed directly to the public Internet. The future private API must authenticate every caller, enforce authorization, rate limits, request validation, CSRF/session protections where applicable, secrets management, and audit requirements.

## Next layers

1. authenticated owner approval service;
2. durable state and audit backend;
3. request/correlation IDs;
4. timeout and concurrency controls;
5. private API;
6. Control Center UI;
7. explicit tool adapters.
