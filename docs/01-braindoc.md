# Braindoc — NodeOps (Smart Traffic Node Companion)

*AiNa Build · Stage 1 (Intake) · 2026-06-20*

### Summary
NodeOps is the single companion application for the entire life of a **Smart
Traffic Node** — a solar-powered, LTE-connected, open-hardware traffic-signal
controller (ESP32 + SIM7600; BME280/BH1750/YL-38 sensors; DS3231 RTC; three
Fotek SSRs driving Red/Amber/Green; 50 W solar + 12 V 10 Ah LiFePO4 in IP65).
It turns capable-but-scattered hardware documentation into one mobile-first,
role-aware, safety-first surface that takes a node from *parts-on-a-bench* to
*years of unattended field operation*. This build delivers the **reference
operator console + mock cloud** (the Cloud↔App seam) that the production iOS/
Android clients and the device firmware integrate against.

### The problem
Everything a person needs to do with a node lives in different places. Building
one means juggling a PDF assembly guide, a BOM spreadsheet, and two JSON
connection maps. Bringing one up means a laptop, a serial terminal, and
hand-running an I²C scan and an SSR test. Operating one means there is no
friendly way to see whether it's online, whether the battery survives the
night, what the signal is showing, or to change a timing plan from the field.
Maintaining a fleet means no map, no alerts, no history — **a dead node is
discovered when someone drives past it.** The hardware is fully documented; the
missing piece is software that runs from a phone at the base of a pole.

### Users
- **Maker / Owner** — built or bought one node (campus, private road, hobby).
  JTBD: bring it up and keep it alive without a lab. Context: single-node,
  "just me" mode, no org.
- **Field Installer / Technician** — commissions nodes on-site. JTBD: pair,
  run bring-up tests, confirm cloud check-in before leaving. Context: at the
  pole, poor signal, needs BLE + offline.
- **Maintenance Crew** — services deployed nodes. JTBD: triage alerts, run
  diagnostics, log service visits. Context: dispatched from a map.
- **Operations / City Manager** — oversees a fleet. JTBD: see fleet health,
  tune timing plans, report uptime. Context: many nodes, RBAC, audit.
- **Administrator** — org, users, roles, SIM/data plans, OTA, integrations.
- **Viewer / Stakeholder** — read-only dashboards, shareable status links.

**Anti-personas**
- General consumers / drivers — they never touch the app.
- Civil-engineering certification bodies — the app exports evidence, it does
  not perform MUTCD/jurisdiction sign-off.
- People wanting a desktop ITS console — v1 is mobile-first (read-only status
  pages excepted).

### V1 scope
**In:**
- Provisioning & pairing (QR + BLE), cellular check-in confirmation, site/group
  assignment, location capture.
- Build & bring-up assistant: four-phase wizard, in-app BOM, wiring/pin maps,
  I²C scan, sensor self-test, SSR pulse test, rail/battery/solar readings,
  commissioning checklist.
- Single-node live monitoring: signal state, online/last-seen, battery SoC +
  runtime, solar, cellular, environment, RTC, one health verdict, history.
- Signal control: view/edit/schedule **versioned timing plans**, adaptive rules,
  flashing/all-red modes, confirmed + time-bounded **manual override**, staged
  push, fail-safe-on-link-loss, plan copy.
- Fleet map + list + search + KPIs; alerts (offline/battery/solar/fault/tamper/
  heat) with ack/snooze/resolve, thresholds, quiet hours, push/email.
- Diagnostics & maintenance, OTA (canary, power-aware, rollback), RBAC + audit,
  offline/stale handling, reporting/exports, energy intelligence.

**Out (deliberate):**
- Automated multi-node green-wave optimization — v1 ships per-node control + the
  data; the optimizer is a later phase (LoRa-mesh stretch).
- Camera / computer-vision traffic-density sensing — no camera in v1 hardware.
- In-app hardware/kit payments & storefront — handled by the campaign site.
- Regulatory certification workflows — app provides audit/exports only.
- Desktop/web operator console as a product — mobile-first (status pages aside).
- Direct carrier/SIM purchasing — v1 shows usage/plan status only.

### Economics
- **Build:** ~10–16 engineer-weeks for the recommended tier (RN app + cloud API
  + device contract), 1–2 engineers. This AiNa package delivers the reference
  cloud console + mock device/cloud seams in the session.
- **Monthly infra:** ~$25–$120 for a small fleet (single VPS + managed Postgres/
  time-series + push/MQTT broker); cellular data is per-SIM and customer-owned.
- **Value:** outage MTTR drops from "next drive-by" (hours-days) to
  push-alert-immediate; bring-up time drops from a laptop session to a guided
  phone walk-through; a soiled panel or aging battery is caught *before* a
  night-time blackout.

### Risks & dependencies
- **Signal-control safety** — any ambiguity resolves to the safest option;
  fail-safe is enforced **on the node**, independent of app/cloud.
- **BLE GATT + device firmware contract drift** — pin the App↔Device and
  Cloud↔App contracts with contract tests; mock both seams.
- **Cellular reliability & data cost** — telemetry cadence is tunable; surface
  SIM usage/caps; distinguish "node offline" vs "phone offline".
- **Energy forecasting accuracy** — depends on an external weather/daylight
  feed; compute server-side, mark predictions as estimates.
- **OTA bricking risk** — signed, resumable, power-aware, canary, rollback.

### DevOps & Deployment
- **Hosting target:** self-hosted Docker image on a single VPS (Hetzner/Fly),
  per the backend golden stack. The production mobile clients ship via App
  Store / Play Store separately.
- **Runtime + framework:** Python 3.12 + FastAPI + Jinja2 + HTMX (reference
  console & mock cloud). Production mobile = React Native (out of this build's
  code, specified in dev notes).
- **Database & persistence:** SQLite for the reference build (zero-config,
  seedable); production → managed Postgres + a time-series store (Timescale)
  for telemetry. Nightly DB dump; telemetry retention policy by tier.
- **Secrets & config:** `APP_NAME`, `NEXT_PUBLIC_REPO_URL` (repo link),
  `DATABASE_URL`, `MQTT_BROKER_URL` (device seam), `WEATHER_API_KEY`
  (energy forecast). Names only.
- **Observability:** console logs + `/healthz` in the reference build; plan
  Sentry + Better Stack uptime in Phase 2 for the cloud.
- **CI/CD:** GitHub Actions → build Docker image → deploy to VPS; mobile via
  EAS build. Reference console: `main` → prod on the VPS.
- **Rollback story:** redeploy the previous Docker image tag (`docker compose
  up -d` with prior tag); OTA firmware has its own canary + rollback path.
- **Scaling envelope:** a single VPS comfortably serves a few hundred nodes'
  console traffic; beyond ~1–2k nodes, move telemetry ingestion to the MQTT
  broker + a worker and split the time-series store.

### Delivery
- **P0** — Provisioning + Bring-up + single-node Monitoring + basic Control +
  Alerts. (Weeks 1–6)
- **P1** — Fleet/Map + RBAC + OTA + Maintenance. (Weeks 6–11)
- **P2** — Energy intelligence + Reports/Integrations + corridor coordination.
  (Weeks 11–16)

**Definition of done (V0 reference console):**
- A seeded fleet renders on a map + list with live-style health verdicts.
- Single-node dashboard shows signal/power/solar/cellular/environment.
- Timing plans can be viewed, edited, staged, and applied with confirmation +
  audit entry; manual override carries a visible expiry.
- Alerts can be acknowledged / snoozed / resolved.
- Bring-up wizard runs I²C-scan / sensor / SSR self-tests against the mock
  device seam and yields a commissioning verdict.

### Open questions
- Which MQTT/broker and time-series store does the customer standardize on?
- Is the external weather/daylight provider chosen (NOAA / OpenWeather / other)?
- Push delivery: APNs + FCM directly, or via a provider (OneSignal/Expo)?
- Org/billing model for SIM data plans — per-org or per-site cost centers?
- Required compliance regime per deployment region (data residency)?

### Assumptions made
- The reference deliverable is the **operator/cloud surface** rendered as a
  server-side web console + mock device/cloud seams — the production mobile
  clients consume the same API and are out of this code package's scope.
- A node's "live" telemetry in the reference build is **simulated** by a mock
  device layer so the full UI is demoable without hardware.
- Single-org demo data is sufficient for V0; multi-tenant RBAC is modeled but
  enforced lightly in the reference build.
- Timing plans, faults, alerts, and audit entries are first-class persisted
  entities even in the reference build.
