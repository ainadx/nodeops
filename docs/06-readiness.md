# Production Readiness — NodeOps

*AiNa Build · Stage 6 (Readiness cluster) · 2026-06-20*

Synthesis of: Deploy Assessor · Onboarding Reviewer · Cost Modeler · DR Planner.

## Deploy readiness scorecard

| Area | V0 reference | Production gate |
|---|---|---|
| Builds & boots | ✅ `uvicorn app.main:app`, 200 on all pages | — |
| Tests | ✅ 13 P0 tests pass | Add contract tests for the 3 seams |
| Containerized | ✅ Dockerfile (honors `$PORT`) | Multi-stage, non-root, healthcheck |
| Auth / RBAC | ⚠️ modeled, not enforced | **Blocking** — enforce server-side |
| Persistence | ⚠️ in-memory (resets) | Postgres + Timescale + backups |
| Device seam | ⚠️ mocked (`sim.py`) | mTLS MQTT broker, signed commands |
| Observability | ⚠️ console + `/healthz` | Sentry + uptime monitor + log store |
| Secrets | ✅ env, gitignored | Vault / platform secret store |
| TLS | ⚠️ none (local) | Caddy/nginx + Let's Encrypt |

**Verdict:** ready for **local/staging demo and stakeholder review now**; the
three ⚠️ "blocking" items (auth/RBAC, persistence, device mTLS) gate a city
pilot.

## Onboarding / first-run
- A new operator lands on `/` and sees a seeded fleet — no empty-state cliff.
- A maker's first job is provisioning: `/fleet` → register → `/bringup` wizard.
  The four-phase steps mirror the documented assembly guide so the app and docs
  never drift (PRD tie-in).
- Health verdicts + the prototype banner make the system state and the "this is
  V0" framing legible immediately.
- **Gap:** no guided first-run tutorial yet (PRD story #6) → Phase 1.

## Cost model (production, small fleet ~50–300 nodes)
| Component | Monthly (USD) |
|---|---|
| App VPS (2 vCPU / 4 GB, Hetzner/Fly) | $15–40 |
| Managed Postgres + Timescale | $15–60 |
| MQTT broker (HiveMQ/EMQX cloud or self-host) | $0–50 |
| Push (APNs free / FCM free / provider) | $0–25 |
| Map tiles (Mapbox free tier → paid) | $0–50 |
| Uptime + error tracking (Better Stack + Sentry free→team) | $0–40 |
| **Cloud subtotal** | **≈ $30–265** |
| Cellular data | per-SIM, customer-owned (tunable cadence) |

Surprise-bill guards: telemetry cadence is tunable per SIM budget; map tiles and
push have free tiers; energy-forecast weather calls (P2) are server-side + cached.

## Disaster recovery
- **Backups:** nightly Postgres dump + Timescale retention policy; store
  off-host; **monthly restore drill** (verify, don't assume).
- **RTO/RPO targets:** RTO ≤ 1 h (redeploy prior image + restore latest dump),
  RPO ≤ 24 h (nightly) — tighten to ≤ 1 h with WAL/PITR for a city pilot.
- **Node-level DR is inherent:** a node fails safe locally regardless of cloud
  state, so a cloud outage degrades *visibility*, not *road safety*.
- **Rollback:** redeploy previous Docker tag; firmware has its own canary +
  rollback path.

## Go / no-go
**GO** for staging + stakeholder demo. **NO-GO** for production control until:
(1) auth + server-side RBAC, (2) durable Postgres + verified backups, (3) mTLS
device identity on the broker. Tracked in `POST_LAUNCH_PHASE1.md`.
