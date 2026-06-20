# NodeOps — Phase 1 Roadmap

### What shipped in V0
- **Provisioning + bring-up + commissioning** — register a node, run I²C/sensor/
  SSR/rail self-tests over the mock BLE seam, gate go-live on a commissioning
  checklist (`/fleet`, `/nodes/{id}/bringup`).
- **Single-node monitoring + fleet map/list/alerts** — live telemetry verdicts,
  a color+shape health map, filterable fleet list, alert lifecycle (`/`, `/map`,
  `/fleet`, `/alerts`).
- **Versioned timing plans + guardrailed control** — stage/apply/override with
  confirmation, auto-expiry, offline-refusal, and an append-only audit log
  (`/nodes/{id}/control`, `/audit`).
- **OTA scaffolding** — power-aware defer + rollback over the mock fleet
  (`/firmware`).

### What's deferred to Phase 1
V0 is the foundation — the operator surface over mock seams. Phase 1 makes it
real: authentication and enforced RBAC, durable persistence, the live device
seam, and the maintenance/energy depth the PRD scopes for P1.

### Phase 1 features (ranked by priority)

#### Feature 1 — Authentication + enforced server-side RBAC
**Why:** the single blocking gate before any real node is controllable. V0 models
roles but fixes `current_user`.
**Acceptance criteria:**
- A user signs in (email/SSO) and gets a session; biometric app-lock on mobile.
- Control routes are rejected (403) for Viewer/Technician where the PRD requires
  Owner/Manager.
- Lost-phone / departed-user access can be revoked instantly server-side.
**Implementation notes:**
- Add an auth dependency to FastAPI; gate `/nodes/*/plan|override|service` and
  `/firmware/*` by role; replace `db.current_user`.
**Complexity:** L · **Depends on:** none

#### Feature 2 — Durable persistence (Postgres + Timescale)
**Why:** state currently resets on restart; telemetry history needs a time-series store.
**Acceptance criteria:**
- Entities persist across restarts; telemetry writes to a hypertable.
- History charts on the node page read real ranges (hours/days/weeks).
**Implementation notes:**
- Move `store.py` entities to SQLModel/SQLAlchemy; keep accessor signatures.
**Complexity:** L · **Depends on:** none

#### Feature 3 — Live device seam (MQTT, mTLS)
**Why:** replace the deterministic mock with real telemetry + commands.
**Acceptance criteria:**
- Node telemetry arrives via the broker; offline detection uses real heartbeats.
- Commands are signed, idempotent, and mutually authenticated.
**Implementation notes:**
- Swap `sim.snapshot` for a broker subscription; add a command publisher.
**Complexity:** L · **Depends on:** Feature 2

#### Feature 4 — History charts & trends
**Why:** operators need to spot battery/solar degradation over time (PRD #35).
**Acceptance criteria:**
- Battery, solar, signal-strength, temperature charts over selectable ranges.
**Implementation notes:**
- Render lightweight inline SVG/Canvas from Timescale aggregates; no heavy JS.
**Complexity:** M · **Depends on:** Feature 2

#### Feature 5 — Alert thresholds, quiet hours & push delivery
**Why:** V0 has the lifecycle but not configurable thresholds or real delivery.
**Acceptance criteria:**
- Per-node/per-fleet thresholds; quiet hours; push + email delivery; escalation.
**Implementation notes:**
- Add a rules table + a notifier; APNs/FCM or a provider behind an interface.
**Complexity:** M · **Depends on:** Feature 1

#### Feature 6 — Diagnostics & maintenance records
**Why:** crews need one-tap full self-test, fault history, and service logs (PRD H).
**Acceptance criteria:**
- A `/nodes/{id}/diagnostics` page aggregates all self-tests into one verdict;
  photos/notes attach to service visits.
**Complexity:** M · **Depends on:** Feature 2

#### Feature 7 — Two-person approval for high-risk actions
**Why:** fleet-wide override/OTA needs a second set of eyes (PRD #85).
**Acceptance criteria:**
- Fleet-wide override/OTA enters a pending state until a second authorized user approves.
**Complexity:** M · **Depends on:** Feature 1

#### Feature 8 — Guided first-run tutorial + maker single-node mode
**Why:** onboarding gap (PRD #5, #6); keep maker and city experiences coherent.
**Acceptance criteria:**
- First-run walkthrough of provision→monitor→control; a lightweight single-node mode skips org setup.
**Complexity:** M · **Depends on:** Feature 1

#### Feature 9 — Read-only shareable status page
**Why:** stakeholders want live status without an account (PRD #94).
**Acceptance criteria:**
- `/status/{id}` renders a public, read-only node/corridor status with no controls.
**Complexity:** S · **Depends on:** none

#### Feature 10 — CSV/PDF exports + uptime/SLA report
**Why:** managers report to stakeholders (PRD M).
**Acceptance criteria:**
- Export fleet/node data as CSV; generate an uptime/incident report over a date range.
**Complexity:** M · **Depends on:** Feature 2

### Beyond Phase 1
- Energy intelligence: runtime forecast (SoC + load + predicted solar), eco mode.
- Corridor / green-wave coordination (depends on multi-node + LoRa-mesh).
- Native mobile clients (React Native) consuming this same API.
- City/ITS integrations via API/webhook; SIM data-plan management.

## How to continue building
- Each feature above is filed as a GitHub issue with an `@claude` mention. The
  Claude Code Action will pick them up and open PRs.
- To request a feature manually, comment `@claude implement Feature N` on the
  repo, or open a new issue starting with `@claude`.
- To pause the autonomous work, remove the `claude-task` label from open issues.
