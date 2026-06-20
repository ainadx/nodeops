# Go-Live Checklist — NodeOps Console

## Infrastructure
- [ ] VPS provisioned (2 vCPU / 4 GB / 20 GB SSD)
- [ ] SSL certificate issued; Caddy/nginx reverse proxy configured
- [ ] DNS A record pointed at server IP
- [ ] Firewall: 80/443 (and 8883 to broker) inbound; 443/8883 outbound

## Application
- [ ] `.env.production` populated (all required vars from the env table)
- [ ] Docker image built from `app/Dockerfile` (no dev deps)
- [ ] `docker compose up -d` succeeds, no restart loops
- [ ] `GET /healthz` returns `ok` within 5s
- [ ] `pytest -q` green (13 P0 tests) on the deployed commit

## Security gates (BLOCKING for production control)
- [ ] Server-side auth + RBAC enforced (no fixed `current_user`)
- [ ] Mutual-TLS device identity on the MQTT broker; commands signed
- [ ] Two-person approval enabled for fleet-wide override / OTA
- [ ] `pip-audit` + Dependabot + secret scanning enabled in CI
- [ ] Control routes NOT reachable without auth from the public internet

## Database (production)
- [ ] Postgres + Timescale provisioned; `pgdata` volume mounted
- [ ] Migrations run successfully; telemetry hypertable + `(node_id, ts)` index
- [ ] First backup taken and **verified restorable**

## Monitoring
- [ ] External uptime monitor on `/healthz`
- [ ] Alert rules: 5xx > 2%/5min, DB down, app restart loop, heartbeat-breach spike
- [ ] **Alert delivery latency measured < 60 s** (node-drop → push)
- [ ] Sentry receiving errors; logs flowing to retention store

## Device & safety
- [ ] A real node fails safe to all-red on link loss / watchdog (HIL verified)
- [ ] Manual override auto-expiry verified on hardware
- [ ] Offline node refuses remote control (verified end-to-end)

## Handover
- [ ] `ops/DEPLOY.md` + `ops/RUNBOOKS.md` committed
- [ ] On-call rotation assigned (≥ 2 people know the runbooks)
- [ ] Product owner signed off on go-live

## Sign-off
| Role | Name | Date |
|------|------|------|
| Tech Lead | | |
| Product Owner | | |
| Safety Reviewer | | |
