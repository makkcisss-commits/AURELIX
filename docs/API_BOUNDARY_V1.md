# AURELIX Private API Boundary V1

## Purpose

The API is the controlled boundary between human interfaces, automation, and the AURELIX core. It is not a direct database shell and it never bypasses the Governor.

## Request Flow

```text
Client
  ↓
Authentication
  ↓
Request Validation
  ↓
Authorization
  ↓
Governor / Policy Engine
  ↓
Domain Service
  ↓
Audit
  ↓
Response
```

## API Rules

1. Every request has an authenticated principal or is explicitly classified as public infrastructure traffic.
2. Every privileged endpoint checks authorization independently of UI controls.
3. The API never accepts a client-supplied role as proof of privilege.
4. Sensitive operations require an idempotency key or equivalent replay protection.
5. Protected actions carry a correlation ID through execution and audit.
6. Validation occurs before a request reaches an external tool.
7. External content is treated as untrusted data, not as policy.
8. Error responses do not disclose credentials, internal secrets, or unnecessary infrastructure details.
9. Rate limits and request-size limits are applied at the boundary.
10. The API fails closed when a mandatory authorization or audit dependency is unavailable.

## Initial Endpoint Domains

```text
/api/v1/system
/api/v1/decisions
/api/v1/opportunities
/api/v1/research
/api/v1/academy
/api/v1/experiments
/api/v1/agents
/api/v1/treasury
/api/v1/audit
/api/v1/identity
```

The concrete framework and persistence layer will be selected only after the domain contracts and security tests are established.

## Owner Approval API

A future approval endpoint must bind an approval to:

- authenticated owner identity;
- exact request ID;
- action type;
- resource scope;
- financial limit where relevant;
- expiration;
- one-time approval identifier.

The UI must display the exact action being approved. A generic "approve everything" control is prohibited for protected operations.

## Web and Mobile

The web control center and future mobile application will be clients of the same API. They will not implement separate business or authorization logic.
