# User Guide — NodeOps Console

*AiNa Build · Stage 8 (Docs cluster) · 2026-06-20*

## Who this is for
Field installers, maintenance crews, and small-city signal operators. No prior
NodeOps knowledge assumed.

## Getting started
1. Open the console (hosted at `http://localhost:7777` in this build).
2. You land on **Overview** — fleet KPIs, the nodes that need attention, and
   recent alerts. The seeded demo fleet has 6 nodes in varied states.

## Provision a new node (Fleet → Provision)
1. Go to **Fleet**. In the right panel, scan the enclosure QR or type the serial,
   give it a name, intersection, and site, then **Register node**.
2. The node starts in **Setup (provisioning)** — it can't go live yet.
3. Click **Start bring-up** to run hardware checks.

## Bring-up & commissioning (`/nodes/{id}/bringup`)
The wizard mirrors the four documented phases (Fabricate → Wire → Bring-up →
Assemble). Under **BLE self-tests**, run each:
- **I²C bus scan** — confirms BME280, BH1750, DS3231 are on the bus.
- **Sensor self-test** — live temperature, humidity, light, rain.
- **SSR output test** — safely pulses Red/Amber/Green.
- **DC rail verification** — 12 V / 5 V / 3.3 V + solar input.

Then **Run commissioning checklist**. A node can only go live once **all required
tests pass** — this gate prevents deploying a half-tested unit. When it passes,
**Confirm check-in** on the node page to bring it online.

## Monitor a node (`/nodes/{id}`)
The dashboard shows the live **signal head** (R/A/G lamps), one **health verdict**
(All good / Needs attention / Critical / Offline), and metric tiles: battery SoC
+ estimated runtime, solar, cellular, RTC, and environment. Telemetry refreshes
every few seconds. **An offline node is clearly marked "stale" — never shown as
live.**

## Control the signal (`/nodes/{id}/control`)
- **Timing plans** are versioned. Editing creates a new version (old ones are
  kept). **Stage** a plan to preview it, or **Apply now** (confirmed) to push it
  live. Every apply is recorded in the audit log.
- **Manual override** forces a phase (e.g. all-red) for a bounded number of
  minutes, then auto-restores the scheduled plan. It shows a live countdown.
- Control on an **offline** node is refused — the node holds its last-known-good
  plan (or fails to all-red) on its own.
- **Service mode** (node page) puts the signal in a safe state while you work,
  then restores it.

## Fleet map & alerts
- **Map** — color + shape coded health pins; pulsing = critical. Tap a pin →
  open the node → **Directions** to dispatch a crew.
- **Alerts** — filter by state; **Acknowledge**, **Snooze**, or **Resolve** each.
  Resolving updates the node's health.

## Firmware (OTA)
**Firmware** lists each node's version. **Update** pushes the latest — but it's
**power-aware**: below 50% battery it **defers** rather than risk stranding the
node. **Roll back** returns a node to the previous version.

## Audit log
Every control, config, and access action is recorded with who/when/what. The log
is append-only.

## Troubleshooting
- *"Node offline" vs "my phone offline"* — the console marks node freshness
  explicitly; if the whole page won't load, it's your connection.
- *Control button disabled* — the node is offline; control needs a live link.
- *Commissioning won't pass* — re-run the failing self-test; the bench/demo node
  has a deliberate I²C fault to show the failure path.
