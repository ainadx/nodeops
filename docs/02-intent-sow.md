# Intent / Statement of Work — NodeOps

*AiNa Build · Stage 2 (Intent cluster) · 2026-06-20*

Synthesis of: Domain Analyst · Scope Architect · Impact Quantifier · Longevity
Critic · Dependency Mapper · Variant Designer.

---

## Domain

**Open-hardware traffic infrastructure / distributed IoT field assets**
(solar + LTE traffic-signal controllers, owned by makers and small cities).

### Dynamics
- The same physical object passes through **four very different jobs** — build,
  bring-up, operate, maintain — usually done by **different people** with
  different tools and skill levels. One app must serve all four without
  becoming four apps.
- The work happens **at a pole, outdoors, often with poor signal.** BLE-local
  and offline-tolerant behavior is not a nicety; it is the primary field
  condition.
- The asset is **safety-bearing.** A wrong signal state is a real-world hazard,
  not a bad UX. This is the single most important domain fact.
- Power is **the binding constraint.** Everything (telemetry cadence, OTA, eco
  mode) bends around "will the battery survive the night."
- Fleets are **sparse and geographically spread.** A map is the natural home
  surface; outages must page, not wait to be noticed.

### Constraints
- **Safety-critical control** — signal changes must be gated, confirmed,
  time-bounded, logged, and fail-safe **on the device** independent of network.
- **Cellular cost & reliability** — per-SIM data budgets cap telemetry cadence.
- **Regulatory adjacency** — the app supports (audit/exports) but does not
  perform MUTCD/jurisdiction certification.
- **Open hardware** — the build assistant must consume the *same* BOM /
  connection-map / assembly-guide source of truth so app and docs never drift.

### What downstream must pay attention to
The product's reputation **is** its safety behavior. Every control/override/
fail-safe ambiguity resolves toward the safest option, even at the cost of
convenience. Scope, data model, and UX must all carry this through.

---

## Executive summary
NodeOps is a single, mobile-first, role-aware companion that takes a Smart
Traffic Node from parts to years of field operation: provision over QR/BLE,
build with a live-checked wizard, monitor power/signal/connectivity, control
timing plans behind safety guardrails, and maintain a fleet from a map with
push alerts. This SOW scopes V1 and recommends a build tier.

## In scope (V1)
- A user can **add a node** by scanning its QR and/or pairing over BLE, set its
  location and site, and **confirm it has checked in to the cloud** before
  leaving.
- A builder can run the **four-phase wizard** and trigger **I²C scan**, **sensor
  self-test**, **SSR pulse test**, and **rail/battery/solar reads** over BLE,
  ending in a **commissioning checklist** that must pass before go-live.
- An operator can see a **single-node dashboard** (signal state, online/last-
  seen, battery SoC + runtime, solar, cellular, environment, RTC) reduced to one
  **health verdict**, plus history.
- An operator can **view/edit/schedule a versioned timing plan**, set adaptive
  rules, enable flashing/all-red, and issue a **confirmed, time-bounded manual
  override** that auto-expires — every action **logged who/when/what**.
- A manager can see a **fleet map + list** with health pins, search, KPIs, and
  receive **push/email alerts** (offline, low battery, solar, fault, tamper,
  heat) that can be **acked/snoozed/resolved** with per-node thresholds + quiet
  hours.
- A technician can run a **full diagnostic self-test**, see **fault history**,
  enter **service mode**, and an admin can push **canary, power-aware OTA** with
  **rollback** and manage **RBAC** with an **immutable audit log**.

## Out of scope (V1, deliberate)
- **Green-wave / corridor optimization engine** — needs multi-node coordination
  (deferred to the LoRa-mesh phase); v1 ships the data + per-node control.
- **Camera / CV traffic-density sensing** — no camera in v1 hardware.
- **In-app kit purchasing / storefront** — owned by the campaign site.
- **Certification workflows** — app exports evidence; it does not certify.
- **Desktop operator console as a product** — mobile-first; read-only status
  pages are the only web-facing exception.
- **Buying SIM/data plans in-app** — usage/plan visibility only.

## Why these boundaries
The split keeps V1 on the **per-node safety + monitoring critical path** and
defers everything that depends on multi-node coordination or hardware NodeOps
doesn't yet have. It honors the domain's central fact (safety) by shipping
guardrailed control first and the "smart corridor" intelligence later, once the
per-node data and control it depends on exist and are trusted.

---

## Impact

**Who benefits**
- *Field installer · faster, surer commissioning · notices:* a phone walk-
  through + live tests replace a laptop + serial terminal; cloud check-in
  confirmed before leaving site.
- *Maintenance crew · outages found in minutes not days · notices:* a push the
  moment a node drops, with a map pin and directions.
- *Ops/city manager · fleet health at a glance + auditable control · notices:*
  one map, uptime KPIs, and a log of every change.
- *Maker/owner · keeps a single node alive · notices:* "will it survive the
  night" answered before the blackout.

**Magnitude (needs validation)**
- Bring-up time: laptop session (~30–60 min/node) → guided ~15 min. *validate.*
- Outage MTTD: hours-to-days (drive-by) → seconds (push). High-confidence.
- Avoided night blackouts: low-battery prediction + eco mode prevent a class of
  total outages that otherwise require a truck roll. *validate frequency.*

**Evidence we have** — the PRD states the current workflow explicitly ("a dead
node is discovered when someone drives past it"; "a laptop, a serial terminal,
and hand-running an I²C scan and SSR test").

**Evidence we'd need** — real fleet size, current MTTR, per-SIM data cost,
truck-roll cost, and how often battery/solar actually cause outages.

**Measurement plan** — track (1) median bring-up time per node, (2) outage MTTD
from drop to acknowledged alert, (3) % of low-battery alerts that prevented a
blackout (alert → intervention before 0% SoC).

---

## Longevity

**3-year outlook** — distributed solar+LTE field assets keep proliferating;
the open-hardware angle and the maker→city continuum is a durable wedge. The
bet is *against* "every city buys a proprietary closed ITS stack" and *for*
"cheap, documented, app-managed nodes spreading at the edges."

**Defensibility** — moderate. The moat is the **tight coupling to documented
hardware** (same BOM/connection-map source of truth) and **safety-grade control
behavior**, not the app UI. Telemetry dashboards are copyable; a trusted
fail-safe control path and a build assistant that never drifts from the docs are
not, quickly.

**Market drift risks**
- *Hardware revision (LoRa mesh, camera, new MCU)* — **slow**; data model must
  not hard-code v1 sensors.
- *Cellular/eSIM economics shift* — **medium**; SIM/plan layer must be swappable.
- *A vendor ships an end-to-end closed competitor* — **slow**; open-hardware +
  self-host is the counter-position.
- *Push/notification platform changes (APNs/FCM policy)* — **fast**; abstract
  delivery behind a provider.

**Kill criteria** — pause if (1) <10 active nodes across all users by month 6;
(2) a safety incident traces to app-side control logic (stop, re-architect);
(3) cellular data cost per node exceeds the value of remote management.

**Verdict** — **Green**, with the standing caveat that *safety behavior is the
product* and must be over-engineered relative to features.

---

## Dependencies

- **Data:** device telemetry (owned by the node/customer), external **weather/
  daylight feed** for energy forecasts, the **BOM/connection-map/assembly-guide**
  artifacts (owned by the hardware project — must be the single source of truth).
- **Vendors:** MQTT broker / IoT hub (device↔cloud), push provider (APNs/FCM or
  OneSignal/Expo), map tiles (Mapbox/Google), managed Postgres + time-series.
  Each is a cost band of low-tens to low-hundreds/month at small fleet scale.
- **Regulatory:** no PII beyond user accounts; location data of public-asset
  poles; data-residency may apply per city deployment; **no certification
  performed**.
- **Distribution:** App Store + Play Store review for the mobile clients; the
  campaign site is the top-of-funnel; BLE pairing depends on OS permission flows.
- **Critical path:** (1) the App↔Device **BLE GATT contract** and the firmware
  fail-safe behavior; (2) the Cloud↔App API + realtime stream; (3) the
  weather/daylight provider for energy intelligence.

---

## Implementation variants

### Variant 1: Lean (tier_lean)
**Budget band (USD):** $8k – $18k
**Engineer-weeks:** 6
**Ops complexity:** low
**Recommended stack family:** fastapi+sqlite (single-node web console + BLE
provisioning helper); mobile deferred
**Target scale:** 1–25 nodes, single operator / maker

**Tradeoffs**
- Ships provisioning + bring-up + single-node monitoring + basic control fast.
- One self-hosted box; minimal infra.
- Gives up fleet map, RBAC, OTA, energy intelligence for v1.
- Maker-grade, not city-grade.

**Kill criteria**
- Customer needs >25 nodes or multi-user RBAC on day one.
- City procurement requires audit + SLA reporting immediately.

### Variant 2: Recommended (tier_recommended)
**Budget band (USD):** $30k – $70k
**Engineer-weeks:** 12
**Ops complexity:** medium
**Recommended stack family:** fastapi cloud + Postgres/Timescale + MQTT; RN
mobile clients; reference console + mock seams delivered first
**Target scale:** 25–300 nodes, small team / small city

**Tradeoffs**
- Covers all of P0 + P1: provisioning, bring-up, monitoring, guardrailed
  control, fleet map, alerts, RBAC, OTA, maintenance.
- Three real seams (Device↔Cloud, Cloud↔App, App↔Device) with mocks + contract
  tests — the safe, testable architecture the PRD asks for.
- Energy intelligence + integrations land in P2.
- More moving parts than Lean; needs a broker + time-series store.

**Kill criteria**
- Budget genuinely capped at maker scale (→ Lean).
- No appetite to run a cloud + broker (→ Lean, BLE-first).

### Variant 3: Hardened (tier_hardened)
**Budget band (USD):** $90k – $180k
**Engineer-weeks:** 20
**Ops complexity:** high
**Recommended stack family:** Variant 2 + HA cloud, two-person approval, SMS/
webhook alerting, energy forecasting, reporting/integrations, HIL firmware test
**Target scale:** 300–2,000 nodes, multi-team city ops

**Tradeoffs**
- Full P0–P2 incl. energy intelligence, reporting/integrations, two-person
  approval, deep OTA canary/rollback, HIL firmware testing.
- City-grade reliability and accountability.
- Highest cost and longest timeline; over-built for a maker.

**Kill criteria**
- Fleet < ~300 nodes (→ Recommended).
- Corridor optimization expected in v1 (still out of scope — re-plan).

### Recommended variant: **tier_recommended**
It matches the PRD's explicit P0+P1 phasing and three-seam architecture without
over-building the energy/integration layer that the PRD itself defers to P2.

### Open questions / risks
- Lock the **BLE GATT** and **Cloud↔App** contracts before parallel dev.
- Choose the **broker + time-series + push provider** trio.
- Confirm the **weather/daylight** provider for energy forecasts (P2).
- Define **data residency / multi-tenant** requirements per city.
- Confirm the BOM/connection-map artifacts are export-stable for the wizard.
