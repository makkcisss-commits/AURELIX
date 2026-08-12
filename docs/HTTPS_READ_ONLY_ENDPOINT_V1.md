# AURELIX HTTPS Read-Only Endpoint V1

## Endpoint contract

```text
GET /v1/control/snapshot
```

Purpose: return the dashboard-safe AURELIX system snapshot to an authenticated owner/service identity.

Example response:

```json
{
  "system": "HEALTHY",
  "governor": "OPERATIONAL",
  "policy": "ACTIVE",
  "audit": "RECORDING",
  "api": "PROTECTED",
  "execution": "GUARDED",
  "budget": "ACTIVE",
  "breaker": "READY"
}
```

Invalid credentials return:

```json
{"error":"authentication_failed"}
```

with HTTP `401`.

## Public endpoints

```text
GET /health
GET /ready
```

`/health` is a minimal liveness response. `/ready` reports whether the service is ready. Neither endpoint exposes internal state or secrets.

## Security boundary

The repository now contains the application-level contract, not a production network listener. A deployment adapter must provide HTTPS/TLS, secure credential/session handling, rate limiting, request limits, security headers, logging/redaction and network access control.

The read-only endpoint has no POST, PUT, PATCH or DELETE operation and cannot approve, spend, execute, modify configuration, or bypass the Governor.

Do not expose this endpoint publicly without an authenticated transport and a private network/access policy appropriate to the deployment.
