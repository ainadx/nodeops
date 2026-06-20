# Ops Runbook (summary) — NodeOps

*AiNa Build · Stage 9 (Ops cluster) · 2026-06-20*

Synthesis of: Deployment Planner · Monitoring Designer · Runbook Writer. The
deployable artifacts live in `ops/` (`DEPLOY.md`, `RUNBOOKS.md`,
`GO-LIVE-CHECKLIST.md`); this is the operator's-eye summary.

## Stack & hosting
- **Unit of deploy:** the `app/` Docker image (FastAPI + Uvicorn), honoring
  `$PORT`. Portable to a Hetzner/Fly VPS behind Caddy/nginx for TLS.
- **Reference build:** stateless, in-memory — start it and it serves. Production
  adds Postgres + Timescale + an MQTT broker (compose services in `ops/DEPLOY.md`).

## Quick deploy
```bash
docker compose up -d --build      # app (+ db/broker in prod compose)
curl -f http://localhost:8000/healthz   # -> ok
```

## Health & monitoring
- **Liveness:** `GET /healthz` → `ok` (wire an external uptime monitor to it).
- **Key signals:** 5xx rate, request latency p95, app restart loops, and — domain-
  specific — **count of nodes breaching the 120 s heartbeat** (a spike means a
  device-seam/broker problem, not an app problem).
- **Alerting:** page on 5xx > 2% for 5 min, `/healthz` down, or DB unreachable.
- **Tools:** Better Stack / UptimeRobot for uptime; Sentry for errors; broker's
  own dashboard for device connectivity. (Phase 2 — console logs only today.)

## SLO targets
- Console availability **99.5%**; `/healthz` p95 < 500 ms.
- **Alert delivery latency < 60 s** from node-drop to push (the critical path).
- Telemetry freshness within the heartbeat window for online nodes.

## Rollback
Redeploy the previous image tag: `docker compose pull && docker compose up -d`
with the prior tag, then confirm `/healthz` + a node page render. Firmware OTA
has its own canary + rollback path (`/firmware`).

## Backup & restore (production)
- Nightly `pg_dump` of Postgres + Timescale retention policy; store off-host.
- Restore drill monthly. RTO ≤ 1 h, RPO ≤ 24 h (tighten with PITR for a pilot).
- **Road safety does not depend on the cloud** — a node fails safe locally, so a
  cloud outage costs visibility, not safety.

See `ops/RUNBOOKS.md` for the 2 a.m. procedures (won't-start, 5xx surge, DB
issues, maintenance window) and `ops/GO-LIVE-CHECKLIST.md` for sign-off.
