# AURELIX production deployment

This stack is ready for a single Docker host. It runs AURELIX, PostgreSQL and Caddy on one private Compose network; only Caddy exposes ports 80/443.

## Prerequisites

- a Linux host with Docker Compose v2;
- a DNS A/AAAA record for `AURELIX_DOMAIN` pointing to the host;
- ports 80 and 443 reachable from the Internet;
- production secrets supplied through the host secret/environment mechanism.

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

## Update

```bash
git pull --ff-only
docker compose --env-file deploy/production/.env \
  -f deploy/production/docker-compose.yml up --build -d
```

## Security boundary

Do not put the production `.env` file in Git. Do not expose port 8000 publicly. Rotate owner/model/research/database credentials independently. Back up the PostgreSQL volume before destructive maintenance.
