# Runbooks — NodeOps Console

## Runbook: Application Won't Start
1. `docker compose ps` — is the `app` container up or restart-looping?
2. `docker compose logs --tail=100 app` — look for Python tracebacks
   (`ModuleNotFoundError`, `TemplateNotFound`, port-in-use).
3. Check env: `.env.production` present and readable; `PORT` not already bound
   (`lsof -i:8000`).
4. (Prod) DB reachable: `docker compose exec db pg_isready` / DSN correct.
5. Escalation: if the image built but won't boot, redeploy the last good tag
   (see Rollback) and page the tech lead.

## Runbook: High Error Rate (5xx)
1. Identify the endpoint: `docker compose logs app | grep ' 500 '` (or Sentry).
2. Common causes on this stack:
   - **TemplateNotFound / Jinja error** after a partial deploy → redeploy clean.
   - **DB pool exhausted / DB down** (prod) → check `db` health, restart `db`.
   - **Broker unreachable** (prod) → telemetry stalls; app still serves
     last-known + marks nodes stale (expected, not a 5xx) — investigate broker.
   - **OOM** → `docker stats`; bump VPS memory.
3. Mitigate: restart the affected service; if a bad deploy, **roll back**.
4. Roll back vs hotfix: roll back if errors started right after a deploy; hotfix
   only for config/env typos.

## Runbook: Database Issues (production)
- **Connection failures:** `docker compose exec db pg_isready`; check pool size
  vs. concurrency; restart `db`; verify `DATABASE_URL`.
- **Slow queries:** `docker compose exec db psql -U postgres nodeops -c "SELECT pid, state, query, now()-query_start AS dur FROM pg_stat_activity ORDER BY dur DESC LIMIT 10;"`
  — telemetry queries should hit the Timescale hypertable index; add/repair
  indices on `(node_id, ts)` if missing.

## Rollback Procedure
```bash
# Standard rollback to the previous container image
docker compose pull
docker compose up -d
curl -f https://<host>/healthz          # expect: ok
docker compose logs --tail=50 app        # confirm clean boot, no restart loop
```

## Backup & Restore
```bash
# Backup (nightly cron)
docker compose exec -T db pg_dump -U postgres nodeops | gzip > /backups/nodeops-$(date +%F).sql.gz
# Restore
gunzip -c /backups/nodeops-<DATE>.sql.gz | docker compose exec -T db psql -U postgres nodeops
```
Back up the `pgdata` volume (DB) and `.env.production`. The app image is
rebuildable from git — no app-state to back up in the reference build.

## Maintenance Window Procedure
- **Maintenance mode:** scale the proxy to serve a 503 page, or
  `docker compose stop app` after announcing the window.
- **DB migrations:** take a backup first; run migrations against `db`; verify on
  a node page before reopening traffic.
- **Per-node service:** use the in-app **Service mode** button — it puts that
  node's signal into a safe state and restores it when done (no window needed).
- **Caches/sessions:** the reference build holds no cache; in prod, clear the
  session store if rotating keys.
