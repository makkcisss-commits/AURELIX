# AURELIX private HTTPS deployment

The repository now contains an ASGI application in `src/aurelix_core/server.py`.

## Local run

Set a secret outside Git:

```bash
export AURELIX_OWNER_ID=owner
export AURELIX_OWNER_SECRET='use-a-long-random-secret'
uvicorn aurelix_core.server:app --host 127.0.0.1 --port 8000
```

The read-only endpoint is:

```text
GET /v1/control/snapshot
Header: X-AURELIX-SECRET: <secret>
```

## HTTPS production boundary

Do not expose the Uvicorn development listener directly to the public Internet. Put it behind a hardened HTTPS reverse proxy/load balancer or a managed private ingress with TLS, access controls and rate limiting.

For production:

1. Store `AURELIX_OWNER_SECRET` in a secret manager.
2. Generate a strong random secret; never commit it.
3. Restrict ingress to the intended private network/VPN or identity-aware gateway.
4. Terminate TLS with a managed certificate.
5. Disable debug/error detail exposure.
6. Add structured audit logging and monitoring.
7. Rotate credentials and provide a recovery path.
8. Keep `/v1/control/snapshot` read-only.

This repository does not claim that a public HTTPS service is deployed. Deployment infrastructure must be configured separately.
