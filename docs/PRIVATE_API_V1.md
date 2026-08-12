# AURELIX Private API V1

The Private API is the controlled boundary between clients and the AURELIX Control Plane.

```text
Client
  ↓
Transport Adapter (future HTTPS server)
  ↓
Private API
  ↓
Authentication
  ↓
Explicit Operation Registry
  ↓
Control Plane / Core
  ↓
Audit
```

## V1 design

The current implementation is intentionally framework-neutral. It authenticates an identity and dispatches only to explicitly registered operations. Unknown operations are denied.

It does not expose arbitrary Python execution, shell commands, model-generated routes, or dynamic imports.

## Production transport requirements

Before deployment, add a dedicated HTTPS transport with:

- TLS;
- secure authentication/session mechanism;
- request size and rate limits;
- structured input validation;
- authentication and authorization middleware;
- CSRF protection where cookie-based browser sessions are used;
- security headers;
- request IDs and audit correlation;
- secret redaction;
- safe error responses;
- health/readiness endpoints that reveal no sensitive data.

The browser must never receive direct authority over core execution. The web application should call narrowly scoped API operations, and every protected operation must continue through the Control Plane gates.
