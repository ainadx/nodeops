# Deployment & Operations Guide — NodeOps Console

## Quick Deploy (Docker Compose)
1. Provision a small VPS (2 vCPU / 4 GB) with Docker + Docker Compose.
2. Point DNS A record at the server; open ports 80/443 inbound.
3. Clone the repo and `cd` to the project root.
4. `cp app/.env.example .env.production` and fill values (see table below).
5. `docker compose up -d --build`
6. `curl -f http://localhost:8000/healthz` → `ok`.
7. Put Caddy/nginx in front for TLS (snippet below).
8. Wire an external uptime monitor to `https://<host>/healthz`.

```yaml
# file: docker-compose.yml  (reference build — single service)
services:
  app:
    build: ./app
    env_file: .env.production
    ports: ["8000:8000"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/healthz').read()==b'ok' else 1)"]
      interval: 30s
      timeout: 5s
      retries: 3
# --- Production adds (uncomment when wiring real seams) ---
#   db:
#     image: timescale/timescaledb:latest-pg16
#     environment: { POSTGRES_DB: nodeops, POSTGRES_PASSWORD: ${DB_PASSWORD} }
#     volumes: ["pgdata:/var/lib/postgresql/data"]
#     restart: unless-stopped
#   broker:
#     image: emqx/emqx:5
#     ports: ["8883:8883"]
#     restart: unless-stopped
# volumes: { pgdata: {} }
```

## Environment Variables
| Var | Required | Controls |
|-----|----------|----------|
| `APP_NAME` | no | Brand shown in the UI (default `NodeOps`) |
| `APP_TAGLINE` | no | Tagline / meta description |
| `PORT` | no | Bind port (default 8000; VPS/Fly inject it) |
| `NEXT_PUBLIC_REPO_URL` | no | Repo link in the prototype banner |
| `DATABASE_URL` | prod | Postgres/Timescale DSN |
| `MQTT_BROKER_URL` | prod | Device↔Cloud broker (mTLS) |
| `WEATHER_API_KEY` | P2 | Energy/runtime forecast feed |
| `PUSH_PROVIDER_KEY` | prod | APNs/FCM or provider |

## Infrastructure Requirements
- **VPS:** 2 vCPU / 4 GB / 20 GB SSD comfortably serves a few hundred nodes' console traffic.
- **Ports:** inbound 80/443 (and 8883 to the broker in prod); outbound 443 (push/weather), 8883 (broker).
- **TLS:** terminate at Caddy/nginx (Let's Encrypt) — the app speaks plain HTTP behind it.
- **Backups:** nightly `pg_dump` + Timescale retention; store off-host; restore drill monthly.

## Health Checks & Monitoring
- Liveness: `GET /healthz` → `ok`.
- Alert on: 5xx > 2% for 5 min · `/healthz` down · DB unreachable · spike in nodes breaching the 120 s heartbeat.
- Tools: Better Stack/UptimeRobot (uptime), Sentry (errors), broker dashboard (device connectivity).

## SLO Targets
- Console availability 99.5%; `/healthz` p95 < 500 ms.
- **Alert delivery < 60 s** node-drop → push (critical path).

## Rollback
```bash
docker compose pull && docker compose up -d   # with the previous image tag
curl -f https://<host>/healthz
```
Firmware OTA rolls back via the `/firmware` UI (canary + previous version).

## Backup & Restore
```bash
# Backup (cron, nightly)
docker compose exec -T db pg_dump -U postgres nodeops | gzip > backup-$(date +%F).sql.gz
# Restore
gunzip -c backup-YYYY-MM-DD.sql.gz | docker compose exec -T db psql -U postgres nodeops
```

## Reverse Proxy (Caddy)
```
your-host.example.com {
    reverse_proxy localhost:8000
}
```
