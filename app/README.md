# NodeOps Console

The reference **operator surface** for Smart Traffic Nodes — the Cloud↔App seam
from the NodeOps PRD, server-rendered with FastAPI + HTMX on the bundled design
system. It runs entirely against two in-process mocks (a mock cloud and a mock
device/BLE) so the full product — provisioning, bring-up self-tests, live
monitoring, guardrailed signal control, fleet map, alerts, OTA, and an immutable
audit log — is demoable without any hardware. The production iOS/Android clients
consume the same routes.

## Quickstart
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
# open http://localhost:8000
```

## Run the tests
```bash
pip install pytest httpx
pytest -q
```

## What's inside
| Path | Role |
|------|------|
| `app/main.py` | FastAPI app — all P0 routes (HTMX fragments + a `/api/*` JSON mirror) |
| `app/store.py` | **Mock cloud** — the entity graph + a seeded single-org fleet |
| `app/sim.py` | **Mock device/BLE** — deterministic telemetry + bring-up self-tests |
| `templates/` | Jinja pages (`pages/`) + HTMX partials (`partials/`) |
| `static/css/app.css` | The golden design system (light + dark) — do not fork |
| `static/css/nodeops.css` | Domain widgets (signal lamps, map, gauges, wizard) |
| `tests/` | pytest suite mapped to the PRD's P0 acceptance criteria |

## Pages
`/` overview · `/fleet` list + provisioning · `/map` health map ·
`/nodes/{id}` live dashboard · `/nodes/{id}/control` timing plans + override ·
`/nodes/{id}/bringup` wizard + BLE self-tests · `/alerts` lifecycle ·
`/firmware` OTA · `/audit` log · `/roadmap`.

## Safety model (mirrored from the PRD)
- Signal-control actions are confirmed, time-bounded, and audit-logged.
- Manual overrides carry an `expires_at` and auto-restore the scheduled plan.
- Control on an **offline** node is **refused** — fail-safe is the node's job.
- Health/signal indicators use **letter + shape** cues, not color alone.

This is a V0 prototype. See `POST_LAUNCH_PHASE1.md` (repo root) for the
issue-ready Phase 1 backlog.
