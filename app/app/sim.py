"""NodeOps mock Device seam — deterministic telemetry + BLE self-tests.

This stands in for the two device-facing seams the PRD describes:

  * **Device <-> Cloud** — live telemetry. `snapshot(node)` synthesises a
    plausible, *moving* reading (signal phase cycles, battery charges by day and
    drains by night, solar tracks daylight) from the node's identity + the wall
    clock, so the dashboards animate without hardware.
  * **App <-> Device (BLE GATT)** — bring-up self-tests. `run_bringup_test()`
    returns I2C-scan / sensor / SSR / rail results exactly as the real GATT
    service would, so the provisioning flow is fully testable against a mock.

Everything here is pure + deterministic given (node, time): the same node at the
same second yields the same reading, which keeps the UI stable between HTMX
polls and makes behaviour testable.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import datetime

from .store import HEARTBEAT_WINDOW, Node, TimingPlan, db, now

PHASES = ["red", "green", "amber"]


def _seed(node: Node) -> float:
    """Stable per-node 0..1 jitter so nodes differ but don't flicker."""
    h = hashlib.sha256(node.serial.encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def is_fresh(node: Node) -> bool:
    return (now() - node.last_seen) <= HEARTBEAT_WINDOW and node.status != "offline"


def current_phase(node: Node, plan: TimingPlan | None, at: datetime) -> str:
    """Where in the R/G/A cycle the signal is right now.

    Overrides win (and are shown as such); a missing/flashing plan flashes red.
    """
    if node.override_phase and node.override_expires_at and node.override_expires_at > at:
        return node.override_phase
    if node.status in ("offline", "provisioning"):
        return "dark"
    if plan is None:
        return "flashing_red"
    cycle = max(1, plan.red_s + plan.amber_s + plan.green_s)
    t = int(at.timestamp()) % cycle
    if t < plan.red_s:
        return "red"
    if t < plan.red_s + plan.green_s:
        return "green"
    return "amber"


@dataclass
class Snapshot:
    fresh: bool
    signal_phase: str
    overridden: bool
    battery_soc: int
    battery_v: float
    runtime_hrs: float
    solar_w: float
    solar_v: float
    solar_a: float
    harvest_wh: int
    cell_rssi: int        # dBm
    cell_bars: int        # 0-4
    carrier: str
    data_mb: float
    temp_c: float
    humidity: int
    pressure: int
    lux: int
    rain: bool
    enclosure_c: int
    rtc_synced: bool
    last_seen: datetime


def _daylight(at: datetime, jitter: float) -> float:
    """0..1 solar-irradiance proxy by hour of day (peak ~13:00)."""
    hour = at.hour + at.minute / 60.0
    x = (hour - 13.0) / 6.0
    base = max(0.0, math.cos(x) ** 2 if -1.6 < x < 1.6 else 0.0)
    return min(1.0, base * (0.85 + 0.3 * jitter))


def snapshot(node: Node) -> Snapshot:
    at = now()
    j = _seed(node)
    fresh = is_fresh(node)
    plan = db.active_plan(node.id)
    phase = current_phase(node, plan, at)

    day = _daylight(at, j)
    solar_w = round(day * (38 + 14 * j), 1)
    solar_v = round(13.2 + 4.0 * day, 1) if solar_w > 1 else 0.0
    solar_a = round(solar_w / solar_v, 1) if solar_v else 0.0
    harvest = int(120 + day * 180 + j * 60)

    # Battery: higher in the afternoon, lower overnight; node-specific offset.
    soc_base = 55 + 35 * (day - 0.2) + 18 * (j - 0.5)
    soc = int(max(8, min(100, soc_base)))
    if node.id == 5:           # the deliberately low-battery node
        soc = 28
    if node.status == "offline":
        soc = max(8, soc - 20)
    batt_v = round(12.0 + (soc / 100.0) * 1.4, 2)
    load_w = 6.5 + (2.0 if phase == "green" else 1.0)
    runtime = round((soc / 100.0) * 120.0 / load_w, 1)  # Wh / W -> hrs

    rssi = -67 - int(18 * (1 - j)) - (40 if node.status == "offline" else 0)
    bars = 0 if node.status == "offline" else max(1, min(4, (rssi + 113) // 12))

    temp = round(16 + 14 * day + 6 * j, 1)
    enclosure = int(temp + 8 + (8 if phase == "green" else 4))
    if node.id == 2:
        enclosure = 51
    rain = (j > 0.78)
    lux = int(day * 90000) + int(200 * j)

    return Snapshot(
        fresh=fresh,
        signal_phase=phase,
        overridden=bool(node.override_phase and node.override_expires_at and node.override_expires_at > at),
        battery_soc=soc,
        battery_v=batt_v,
        runtime_hrs=runtime,
        solar_w=solar_w if fresh else 0.0,
        solar_v=solar_v,
        solar_a=solar_a,
        harvest_wh=harvest,
        cell_rssi=rssi,
        cell_bars=bars,
        carrier="—" if node.status == "offline" else ("AT&T" if j > 0.5 else "T-Mobile"),
        data_mb=round(140 * (0.4 + j), 1),
        temp_c=temp,
        humidity=int(45 + 30 * (1 - day) + 10 * j),
        pressure=int(1009 + 8 * j),
        lux=lux,
        rain=rain,
        enclosure_c=enclosure,
        rtc_synced=(node.id != 4),
        last_seen=node.last_seen,
    )


def health_verdict(node: Node) -> tuple[str, str, str]:
    """Reduce a node to one verdict. Returns (key, label, badge-class).

    key: good | attention | critical | offline | setup
    """
    if node.status == "provisioning":
        return "setup", "Setup", "badge"
    if node.status == "maintenance":
        return "attention", "Service mode", "badge--warning"
    if not is_fresh(node) or node.status == "offline":
        return "offline", "Offline", "badge--danger"
    open_a = db.node_alerts(node.id)
    if any(a.severity == "critical" and a.state == "open" for a in open_a):
        return "critical", "Critical", "badge--danger"
    snap = snapshot(node)
    if snap.battery_soc < 30 or any(a.state == "open" for a in open_a):
        return "attention", "Needs attention", "badge--warning"
    return "good", "All good", "badge--success"


# ── App <-> Device (BLE GATT) mock — bring-up self-tests ──────────────────
def run_bringup_test(node: Node, test: str) -> dict:
    """Execute a bring-up self-test as the BLE GATT service would.

    Returns {"pass": bool, "title": str, "lines": [str], "detail": str}.
    Deterministic per node; the offline/uncommissioned bench node is the one
    that exercises the failure path.
    """
    j = _seed(node)
    snap = snapshot(node)
    flaky = (node.status == "provisioning" and j < 0.6)

    if test == "i2c":
        found = ["0x76 BME280 (temp/humidity/pressure)",
                 "0x23 BH1750 (ambient light)",
                 "0x68 DS3231 (RTC)"]
        if flaky:
            found = found[:1] + ["0x23 BH1750 — NOT DETECTED (check SDA/SCL)"]
        ok = all("NOT DETECTED" not in x for x in found)
        return {"pass": ok, "title": "I2C bus scan",
                "lines": found,
                "detail": "3/3 sensors on the bus" if ok else "Sensor missing — re-seat I2C wiring"}

    if test == "sensors":
        lines = [f"Temperature: {snap.temp_c} C",
                 f"Humidity: {snap.humidity}%",
                 f"Ambient light: {snap.lux:,} lux",
                 f"Rain: {'detected' if snap.rain else 'dry'}"]
        ok = not flaky
        return {"pass": ok, "title": "Sensor self-test", "lines": lines,
                "detail": "All sensor reads sane" if ok else "BH1750 read failed"}

    if test == "ssr":
        lines = ["RED  SSR -> pulsed 400ms -> OK",
                 "AMBER SSR -> pulsed 400ms -> OK",
                 "GREEN SSR -> pulsed 400ms -> OK"]
        return {"pass": True, "title": "SSR output test", "lines": lines,
                "detail": "All three relays switched; lamps confirmed"}

    if test == "rails":
        v12 = round(12.0 + (snap.battery_soc / 100) * 1.4, 2)
        lines = [f"12V rail: {v12} V (battery)",
                 f"5V rail: 5.0{int(j*9)} V",
                 "3.3V rail: 3.31 V",
                 f"Solar in: {snap.solar_w} W @ {snap.solar_v} V"]
        return {"pass": True, "title": "DC rail verification", "lines": lines,
                "detail": "All rails within tolerance"}

    if test == "commission":
        # Aggregate: a node is commission-ready only if every required test passed.
        required = ["i2c", "sensors", "ssr", "rails"]
        passed = sum(1 for t in required if node.bringup.get(t, {}).get("pass"))
        ok = passed == len(required)
        lines = [f"{t.upper()}: {'PASS' if node.bringup.get(t, {}).get('pass') else 'not run / FAIL'}"
                 for t in required]
        return {"pass": ok, "title": "Commissioning checklist",
                "lines": lines,
                "detail": f"{passed}/{len(required)} required tests passing"
                          + (" — ready to go live" if ok else " — cannot go live yet")}

    return {"pass": False, "title": "Unknown test", "lines": [], "detail": "No such test"}
