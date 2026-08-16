# AURELIX production deployment

This stack is designed for a single Docker host. AURELIX runs with its durable SQLite runtime database on a named volume, while Caddy is the only Internet-facing service and exposes ports 80/443.

PostgreSQL is **not** part of the production persistence path yet. The runtime currently implements SQLite persistence; an environment variable cannot make PostgreSQL active. PostgreSQL support must not be declared production-ready until the runtime store and its integration tests actually use it.

## Prerequisites

- a Linux host with Docker Compose v2;
- a DNS A/AAAA record for `AURELIX_DOMAIN` pointing to the host;
- ports 80 and 443 reachable from the Internet;
- production secrets supplied through the host secret/environment mechanism;
- a backup mechanism for the `runtime_data` volume.

Caddy will obtain and renew the public TLS certificate automatically when the configured hostname resolves to the host and ports 80/443 are reachable.

## Start

From the repository root:

```bash
cp deploy/production/.env.example deploy/production/.env
# edit deploy/production/.env using a secret manager or protected host environment

docker compose --env-file deploy/production/.env \
  -f deploy/production/docker-compose.yml up --build -d
```

## Verify

```bash
docker compose --env-file deploy/production/.env \
  -f deploy/production/docker-compose.yml ps

curl -fsS https://$AURELIX_DOMAIN/health
```

The protected control plane requires the configured `AURELIX_OWNER_SECRET` in the `X-AURELIX-SECRET` header. The application container is not published directly to the host.

## Backup / restore

The authoritative runtime state is the `runtime_data` Docker volume. Backups must include that volume before upgrades or destructive maintenance, and a restore drill must be performed before claiming disaster-recovery readiness.

## Update

```bash
git pull --ff-only
docker compose --env-file deploy/production/.env \
  -f deploy/production/docker-compose.yml up --build -d
```

## Security boundary

Do not put the production `.env` file in Git. Do not expose port 8000 publicly. Rotate owner/model/research credentials independently. Do not advertise PostgreSQL as active until a real PostgreSQL-backed RuntimeStore exists and passes integration, restart, concurrency and recovery tests.
