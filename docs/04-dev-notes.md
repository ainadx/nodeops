# Dev Notes — NodeOps Console

*AiNa Build · Stage 4 (Dev cluster) · 2026-06-20*

## What was built
A working, server-rendered **NodeOps operator console** that implements every
P0 feature from the PRD against two in-process mocks, so the whole product is
demoable with no hardware and no network. Verified running
(`uvicorn app.main:app`), all pages return 200, and a 13-case pytest suite
mapped to the P0 acceptance criteria passes.

> **Why a web console, not React Native?** The PRD's product is a cross-platform
> mobile app, but it is *backend-heavy* (fleet telemetry, control, RBAC, audit,
> OTA). The AiNa golden stack for backend-heavy work is FastAPI + HTMX. So this
> build delivers the **Cloud↔App seam** — the operator surface + the mock cloud
> and device seams the mobile clients and firmware integrate against. It is the
> reference implementation and the test harness, not the shipping mobile binary.

## Architecture
Three seams, exactly as the PRD specifies — two of them mocked here so the third
(the UI) is testable in isolation:

```
 ┌─────────────┐   App↔Device (BLE GATT)   ┌──────────────┐
 │ sim.py      │◀──────────────────────────│  Bring-up    │
 │ MOCK DEVICE │   I²C scan / sensor / SSR  │  wizard      │
 │  + telemetry│                            └──────────────┘
 └─────┬───────┘
       │ Device↔Cloud (telemetry, deterministic)
 ┌─────▼───────┐   Cloud↔App (REST + HTMX)  ┌──────────────┐
 │ store.py    │◀──────────────────────────▶│  main.py     │
 │ MOCK CLOUD  │                            │  FastAPI UI  │──▶ browser / mobile
 │ entity graph│                            │  + /api/*    │
 └─────────────┘                            └──────────────┘
```

- **`app/store.py` — mock cloud.** The full entity graph (Organization → Sites →
  Nodes; Telemetry, TimingPlan, Alert, Event, MaintenanceRecord,
  FirmwareRelease, OtaJob, AuditEntry, User) plus a seeded single-org fleet of 6
  nodes in deliberately varied health states (one offline, one low-battery, one
  soiled-solar, one bench/provisioning). `HEARTBEAT_WINDOW=120s`,
  `OVERRIDE_MAX=30min`.
- **`app/sim.py` — mock device + BLE.** Pure, deterministic functions:
  `snapshot(node)` synthesises moving telemetry (signal phase cycles from the
  active plan; battery charges by day / drains by night; solar tracks a daylight
  curve); `run_bringup_test()` returns I²C/sensor/SSR/rail results as the GATT
  service would; `health_verdict()` reduces a node to one of
  good/attention/critical/offline/setup.
- **`app/main.py` — FastAPI.** ~29 routes. HTMX endpoints return HTML fragments
  (rows, cards, toasts); a thin `/api/nodes` JSON mirror is what the mobile
  client / integrations would call. Toasts go through the starter's `_toast()`
  helper to keep the `X-Toast` header ASCII-safe.

## How to run
```bash
cd app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000     # currently hosted on :7777
pip install pytest httpx && pytest -q          # 13 passed
```

## P0 verification (all PASS)
| PRD feature | Where | Evidence |
|---|---|---|
| Provisioning & claim | `POST /nodes`, `/nodes/{id}/checkin` | register → `provisioning`; check-in **refused** until commissioned |
| Bring-up self-tests | `/nodes/{id}/bringup/{test}` | I²C lists BME280/BH1750/DS3231; SSR pulses R/A/G; rails read 12/5/3.3V; bench node exercises the FAIL path |
| Commissioning gate | `/nodes/{id}/bringup/commission` | go-live blocked until required tests pass |
| Single-node dashboard | `/nodes/{id}` + `/telemetry` poll | live metrics; offline node renders **stale**, not live |
| Versioned timing plans | `POST /nodes/{id}/plan` | edit creates a new version; old retained; apply confirmed + audited |
| Safe control | apply / override | offline node **refuses** control; override carries `expires_at` + countdown, clamped to 30 min |
| Fleet map/list/search/KPIs | `/`, `/fleet`, `/map` | filter by status/site, search by serial, color+shape pins |
| Alerts lifecycle | `/alerts/{id}/{ack,snooze,resolve}` | open→ack→resolved |
| RBAC + audit | `/audit` | every control/config action appended, no edit/delete route |
| OTA (P1) | `/firmware/{id}/update` | power-aware **defer** below 50% SoC; **rollback** route |

## What's stubbed / simplified vs. production
- **Telemetry is simulated** deterministically (no real MQTT). Swap `sim.snapshot`
  for a broker subscription; the route layer is unchanged.
- **Persistence is in-memory** (resets on restart). Move `store.py` entities to
  Postgres + Timescale; accessor functions are the seam.
- **RBAC is modeled, lightly enforced.** `db.current_user` is fixed to a Manager;
  production evaluates permissions server-side per request and gates control
  routes by role.
- **Auth / biometrics / push / weather forecast** are out of the reference build
  (P1/P2); env placeholders exist in `.env.example`.
- **Real fail-safe lives on the node.** Here it's mirrored as "refuse control
  when offline"; the firmware enforces watchdog → all-red independently.

## Notable decisions
- Health and signal indicators carry a **letter glyph + shape**, never color
  alone (a11y / color-blind requirement #104).
- Editing a plan is **never destructive** — it always mints a new version, which
  is what makes staging, copy, and rollback first-class.
- The prototype banner is non-dismissable and links to `@claude` issues so the
  repo can keep evolving post-handoff.
