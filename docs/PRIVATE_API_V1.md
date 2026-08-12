# AURELIX Private API V1

The Private API is the controlled boundary between clients and the AURELIX Control Plane.

```text
Client
  ↓
HTTPS Transport Adapter
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

## Current boundary

The framework-neutral API authenticates a caller and dispatches only explicitly registered operations. Unknown operations are denied. It does not expose arbitrary Python execution, shell commands, model-generated routes, or dynamic imports.

The HTTP contract currently provides only minimal health/readiness and safe-error primitives. This is intentional: transport wiring should be added only after authentication, authorization, input validation, rate limiting, request correlation, and secure secret handling are defined.

## Production transport requirements

Before deployment:

- HTTPS/TLS;
- secure authentication/session mechanism;
- request size and rate limits;
- strict input validation;
- authorization middleware;
- CSRF protection for cookie-based browser sessions;
- security headers;
- request/correlation IDs;
- secret redaction;
- safe error responses;
- health/readiness endpoints with no sensitive details.

The browser must never receive direct authority over core execution. The web application calls narrowly scoped API operations, and protected operations continue through the Control Plane gates.
