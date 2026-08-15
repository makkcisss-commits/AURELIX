# AURELIX System Integrity Control Plane v1

AURELIX keeps one canonical composition root. The integrity control plane is an additive read-only safety layer over the existing `EngineFactory`, `SystemDiagnostics` and `SystemValidation` authorities.

## Rules

1. **One responsibility, one live owner.** Shared Runtime engines must point to the EngineFactory-owned instance.
2. **Replacement, not coexistence.** A replacement implementation must be wired at the composition root; an old live owner must not remain active for the same responsibility.
3. **One runtime execution authority.** A job kind cannot be registered in both the normal and claimed-handler registries.
4. **Unique schedule identity.** A schedule name is an identity; duplicate registrations are an integrity failure.
5. **Durable state is checked.** Persisted mission-resume records must be valid JSON and obey their state contract. A legacy `reserved` record without lease metadata is unsafe and is reported as a failure rather than guessed as recoverable.
6. **No autonomous silent repair of critical state.** The controller reports deterministic findings. Critical replacement/migration remains subject to the existing change-management and approval gates.

## Verdicts

- `ok`: all inspected invariants hold.
- `warning`: the system is usable but a non-critical condition needs attention.
- `failed`: a protected invariant is violated; the system must not be declared ready.

`EngineFactory.check_integrity()` is the programmatic entry point. `SystemValidation` and `SystemDiagnostics` include the same verdict so health, validation and integrity cannot silently disagree.

## Final-proof principle

AURELIX is considered ready only after the control plane reports no critical findings and the complete CI/system-regression suite passes. CI green alone is not sufficient when a deterministic architectural invariant is violated.
