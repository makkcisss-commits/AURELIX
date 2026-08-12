# AURELIX local deployment

AURELIX now includes a runnable ASGI server, a live read-only control center, and a minimal Docker Compose deployment.

## Local Python run

Set a secret outside Git:

```bash
export AURELIX_OWNER_ID=owner
export AURELIX_OWNER_SECRET='use-a-long-random-secret'
python -m pip install -r requirements.txt
python -m pip install -e .
aurelix-server
```

Open `http://127.0.0.1:8000/` for the control center. Enter the same owner secret to read the protected runtime snapshot.

## Docker Compose

From the repository root:

```bash
export AURELIX_OWNER_SECRET='use-a-long-random-secret'
docker compose -f deploy/docker-compose.yml up --build -d
```

The container serves the web UI and API on port `8000`, with SQLite state persisted in the `aurelix_data` volume.

Optional model and research providers are enabled by setting their corresponding `AURELIX_*` environment variables. Without them, the authenticated read-only control plane can still start and report that the providers are not configured.

## Protected API

```text
GET /v1/control/snapshot
Header: X-AURELIX-SECRET: <secret>
```

## Production boundary

Do not expose the Uvicorn listener directly to the public Internet. Put it behind a hardened HTTPS reverse proxy/load balancer or managed private ingress with TLS, access controls and rate limiting.

Production still requires a secret manager, TLS termination, monitoring, credential rotation and an explicit deployment environment. The repository does not claim that a public HTTPS service is already deployed.
