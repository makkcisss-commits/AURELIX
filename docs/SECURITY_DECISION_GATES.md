# AURELIX Security Decision Gates

## Purpose

This document defines the security gates that every privileged AURELIX action must pass before execution.

## Gate Model

```text
REQUEST
  ↓
IDENTITY
  ↓
AUTHORIZATION
  ↓
POLICY
  ↓
RISK
  ↓
RESOURCE SCOPE
  ↓
APPROVAL (if required)
  ↓
RATE / BUDGET LIMITS
  ↓
AUDIT RECORD
  ↓
EXECUTION
  ↓
RESULT VERIFICATION
```

A failed gate is a denial or a request for additional authorization. It is never an implicit approval.

## Risk Classes

### R0 — Observation
Read-only, non-sensitive observation. No external side effect.

### R1 — Reversible Internal Action
A bounded internal action with a tested rollback path.

### R2 — External Side Effect
Actions that communicate externally, publish content, modify an external service, or consume a bounded resource.

### R3 — Sensitive / Material Action
Financial expenditure, privilege changes, production security changes, or actions with significant business impact.

### R4 — Critical Action
Actions affecting ownership, core governance, security root controls, irreversible material changes, or emergency controls.

## Default Approval Matrix

| Risk | Default autonomy | Owner approval |
|---|---|---|
| R0 | A0-A1 | No |
| R1 | A2 | Usually no, if policy permits |
| R2 | A2-A3 | Policy-dependent |
| R3 | A3 | Yes |
| R4 | A4 | Yes, explicit |

The matrix is a default. A stricter policy may always raise the required authorization level.

## Financial Gate

Every material expenditure must have:

- unique request ID;
- project and business purpose;
- supplier;
- amount and currency;
- recurrence information;
- expected benefit / ROI estimate;
- risk assessment;
- lower-cost alternatives;
- evidence;
- explicit authorization when required.

An approval is scoped to the request. It cannot be silently reused for another transaction.

## AI Agent Rule

An agent output is a proposal or instruction candidate, not an authorization credential. External content, model output, retrieved documents, and tool responses cannot elevate privileges.

Agents receive only the minimum tools and permissions necessary for their assigned task. This follows least-privilege and excessive-agency guidance from NIST and OWASP. 

## Fail Closed

If a required identity, authorization, policy, audit, budget, or approval service is unavailable, a protected action must not execute by default.

## Verification

After execution, the system should verify the observed result against the intended action and record discrepancies. A successful API call is not automatically proof that the business objective succeeded.

## Audit

Each gate decision should be associated with a correlation ID and record the actor, action, resource, policy result, approval state, timestamp, and outcome.
