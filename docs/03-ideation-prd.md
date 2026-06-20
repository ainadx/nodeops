# PRD (Synthesized) — NodeOps

*AiNa Build · Stage 3 (Ideation cluster) · 2026-06-20*

Synthesis of: Domain Architect · Stack Selector · Data Modeler · API Designer ·
UI/UX Composer · NFR Specialist. This is the spec the Dev cluster scaffolds from.

### Name
**NodeOps Console**

### Elevator pitch
NodeOps is the single companion for a Smart Traffic Node's whole life — build,
bring-up, operate, monitor, maintain. This build delivers the **operator console
+ mock cloud/device seams** that the production iOS/Android clients and the node
firmware integrate against.

### Chosen variant
`tier_recommended`

### Tech stack (one-line)
FastAPI + Jinja2/HTMX · server-rendered design-system UI · SQLite (reference) / Postgres+Timescale (prod) · Docker on a VPS

---

## Architectural posture
Server-rendered monolith for the reference console (FastAPI + HTMX), realtime-
*flavored* via HTMX polling of a **mock device/cloud layer** that simulates live
telemetry deterministically. The production system is the same Cloud↔App REST +
realtime API consumed by a React Native mobile client, plus a Device↔Cloud MQTT
seam and an App↔Device BLE GATT seam — all three mockable for test. Data is
mostly **tabular records + small time-series** (telemetry snapshots, history).
Mobile-first information architecture; safety-first control flows.

---

## Features

- **Provisioning & node claim** [P0]
  - what: add a node by QR/serial or BLE pairing, set location + site, confirm
    cloud check-in.
  - acceptance: posting a serial creates a node in `provisioning`; a "check-in"
    action flips it to `online` with a `last_seen`; it then appears on fleet +
    map.
  - depends on: Node, Site · `POST /nodes`, `POST /nodes/{id}/checkin` · /fleet, /map

- **Build & bring-up assistant** [P0]
  - what: four-phase wizard with BLE-style self-tests against the mock device.
  - acceptance: running **I²C scan** lists detected sensors (BME280/BH1750/
    DS3231); **sensor self-test** returns live temp/humidity/light/rain;
    **SSR test** pulses R/A/G and reports pass; **rail read** returns 12/5/3.3 V;
    the **commissioning checklist** blocks go-live until all required tests pass.
  - depends on: Node, Event · `POST /nodes/{id}/bringup/{test}` · /nodes/{id}/bringup

- **Single-node live dashboard** [P0]
  - what: signal state, online/last-seen, battery SoC+runtime, solar, cellular,
    environment, RTC, reduced to one health verdict; history sparkline.
  - acceptance: the page shows the active R/A/G phase and a single
    `all good | needs attention | critical` verdict derived from telemetry +
    open alerts; a node not seen within the heartbeat window renders **offline**.
  - depends on: Node, Telemetry, Alert · `GET /nodes/{id}`, `GET /nodes/{id}/telemetry` · /nodes/{id}

- **Timing plans (versioned) & safe control** [P0]
  - what: view/edit/stage/apply a versioned timing plan; flashing/all-red modes;
    confirmed, time-bounded manual override that auto-expires.
  - acceptance: editing a plan creates a **new version** (old retained); applying
    requires explicit confirmation and writes an **audit entry**; an **override**
    records an `expires_at` and the UI shows a countdown; control on an offline
    node is **refused** with a safety message.
  - depends on: Node, TimingPlan, AuditLog · `POST /nodes/{id}/plan`, `POST /nodes/{id}/override` · /nodes/{id}/control

- **Fleet map + list + KPIs + search** [P0]
  - what: color/shape-coded health pins on a map, a sortable/filterable list,
    fleet KPIs, search by name/intersection/site/serial.
  - acceptance: the list filters by status and site; KPIs show nodes online /
    on-battery / open alerts / uptime%; searching a serial jumps to the node.
  - depends on: Node, Site, Alert · `GET /fleet`, `GET /map`, `GET /search` · /fleet, /map

- **Alerts: lifecycle + thresholds** [P0]
  - what: alerts for offline/low-battery/solar/fault/tamper/heat with
    acknowledge / snooze / resolve and per-node thresholds + quiet hours.
  - acceptance: an alert can move `open → acknowledged → resolved`; snooze sets a
    `snoozed_until`; resolving an alert updates the node's health verdict.
  - depends on: Alert, Node · `POST /alerts/{id}/{action}` · /alerts

- **RBAC + immutable audit log** [P0]
  - what: roles (Owner/Manager/Technician/Viewer); every control/config/access
    change is logged who/when/what.
  - acceptance: control actions appear in `/audit` with actor, node, action,
    timestamp; the audit log is append-only (no edit/delete route).
  - depends on: User, AuditLog · `GET /audit` · /audit

- **Diagnostics & maintenance** [P1]
  - what: one-tap full self-test, fault history, service mode, maintenance log.
  - acceptance: full self-test aggregates the bring-up tests into one verdict;
    service mode marks the node `maintenance` (safe state) and back.
  - depends on: Node, Event, MaintenanceRecord · `/nodes/{id}/diagnostics`

- **OTA firmware (canary, power-aware, rollback)** [P1]
  - what: see firmware version + availability; push to node/group; defer on low
    power; roll back.
  - acceptance: an OTA job records target version, defers if SoC < threshold,
    and can roll back to the prior version.
  - depends on: Node, FirmwareRelease, AuditLog · `/firmware`

- **Energy intelligence** [P2]
  - what: runtime forecast (SoC + load + predicted solar), energy reports,
    recommendations, eco mode.
  - depends on: Telemetry, external weather feed.

- **Reporting & integrations** [P2]
  - what: uptime/SLA reports, CSV/PDF export, API/webhook, SIM usage, status page.
  - depends on: all entities · `/api/*`, `/status/{id}`.

---

## Data model summary
- **Organization** — top-level tenant.
- **Site** — a group/corridor of nodes within an org.
- **Node** — a physical controller; status, location, firmware, health.
- **Telemetry** — time-series + latest snapshot (signal, power, solar, cellular,
  environment, RTC) per node.
- **TimingPlan** — versioned phase durations + schedule bindings + adaptive
  rules; staged/applied/active flags.
- **Alert** — raised condition with severity + lifecycle state.
- **Event** — bring-up/diagnostic/fault log entries per node.
- **MaintenanceRecord** — service visits, notes.
- **FirmwareRelease** — versions + OTA job state.
- **AuditLog** — append-only record of control/config/access actions.
- **User** — account + role scoped to org/site.

(Full field detail in `04-dev-notes.md` and the code's `app/models.py`.)

## API contract summary
- `/nodes`, `/nodes/{id}`, `/nodes/{id}/checkin`, `/nodes/{id}/telemetry`
- `/nodes/{id}/bringup/{test}` (i2c | sensors | ssr | rails | commission)
- `/nodes/{id}/plan`, `/nodes/{id}/override`
- `/fleet`, `/map`, `/search`
- `/alerts`, `/alerts/{id}/{ack|snooze|resolve}`
- `/audit`, `/firmware`, `/healthz`

HTMX endpoints return **HTML fragments** (rows, cards, toasts); a thin JSON
surface under `/api/*` mirrors the same data for the mobile client / integrations.

## NFR highlights
- **Control safety (non-negotiable):** every signal-control action is
  idempotent, confirmed, time-bounded, logged; overrides auto-expire; control is
  refused when the node is offline; fail-safe is the node's responsibility in
  production (modeled in the mock here).
- **Staleness honesty:** telemetry older than the heartbeat window renders
  **stale/offline** explicitly; never show old values as live.
- **RBAC server-side:** permissions evaluated server-side, never trusted from
  the client (modeled; lightly enforced in the reference build).
- **Accessibility first-class:** health/signal indicators carry **shape + label**
  cues, not color alone; dark mode inherited from the design system.
- **Observability:** `/healthz`, structured console logs; Sentry in Phase 2.

## Open questions
- Heartbeat window length (offline threshold) — default **120 s**; confirm.
- Override max timeout ceiling — default **30 min**; confirm.
- Low-battery OTA-defer threshold — default **SoC < 50 %**; confirm.
- Broker / time-series / push provider choices (prod).
- Weather/daylight provider for energy forecast (P2).

## What's NOT in V1 (deliberate)
- Green-wave/corridor optimization (data + per-node control only).
- Camera/CV density sensing (no hardware).
- In-app kit payments / storefront.
- Certification workflows (export evidence only).
- Buying SIM/data plans in-app.
