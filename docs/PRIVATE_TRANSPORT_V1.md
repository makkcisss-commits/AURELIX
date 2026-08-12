# AURELIX Private Transport V1

The transport adapter is the final boundary before a future HTTPS server reaches the framework-neutral Private API.

```text
HTTPS server (future)
        ↓
PrivateTransport
        ↓
PrivateApi
        ↓
Authentication
        ↓
Registered operation
        ↓
Control Plane
```

## Fail-closed behavior

Authentication or operation failures are returned as a generic `403 forbidden` response so the transport does not disclose whether an identity, credential, or operation exists.

The adapter does not execute code, load plugins, or dynamically dispatch arbitrary names.

## Before deployment

A production server must add TLS, secure session/token handling, request limits, input validation, CSRF protection where applicable, security headers, rate limiting, request correlation IDs, structured audit events, secret redaction, and safe health/readiness endpoints.

The transport must remain private. The public Internet should never be able to reach the Core directly.
