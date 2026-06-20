"""NodeOps reference data store — the mock Cloud seam.

An in-memory, deterministic stand-in for the production cloud (Postgres +
Timescale + MQTT). It holds the entity graph the PRD specifies —
Organization -> Sites -> Nodes, plus Telemetry, TimingPlans, Alerts, Events,
MaintenanceRecords, FirmwareReleases and an append-only AuditLog — and seeds a
small, realistic single-org fleet so every screen is demoable without hardware.

The store is intentionally plain Python (lists of dataclasses) so the whole app
boots with `uvicorn app.main:app` and no DB. In production these same entities
move to Postgres; the route layer is written against these accessor functions so
the swap is mechanical.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

UTC = timezone.utc


def now() -> datetime:
    return datetime.now(UTC)


# ── Entities ──────────────────────────────────────────────────────────────
@dataclass
class Organization:
    id: int
    name: str


@dataclass
class Site:
    id: int
    org_id: int
    name: str
    corridor: str


@dataclass
class Node:
    id: int
    serial: str
    name: str
    intersection: str
    site_id: int
    status: str            # provisioning | online | offline | maintenance
    lat: float
    lon: float
    firmware: str
    commissioned: bool
    last_seen: datetime
    # control state
    override_phase: str | None = None
    override_expires_at: datetime | None = None
    override_by: str | None = None
    # bring-up test results: test_key -> {"pass": bool, "detail": str, "ts": iso}
    bringup: dict = field(default_factory=dict)


@dataclass
class TimingPlan:
    id: int
    node_id: int
    version: int
    name: str
    red_s: int
    amber_s: int
    green_s: int
    schedule: str
    adaptive_rules: str
    active: bool = False
    staged: bool = False
    created_at: datetime = field(default_factory=now)
    created_by: str = "system"


@dataclass
class Alert:
    id: int
    node_id: int
    kind: str              # offline | low_battery | solar | fault | tamper | heat
    severity: str          # critical | warning | info
    message: str
    state: str = "open"    # open | acknowledged | snoozed | resolved
    created_at: datetime = field(default_factory=now)
    snoozed_until: datetime | None = None


@dataclass
class Event:
    id: int
    node_id: int
    kind: str              # bringup | diagnostic | fault | service
    detail: str
    ts: datetime = field(default_factory=now)


@dataclass
class MaintenanceRecord:
    id: int
    node_id: int
    tech: str
    note: str
    ts: datetime = field(default_factory=now)


@dataclass
class FirmwareRelease:
    version: str
    notes: str
    is_latest: bool = False


@dataclass
class OtaJob:
    id: int
    node_id: int
    target_version: str
    state: str             # queued | deferred | applying | done | rolled_back
    reason: str = ""
    ts: datetime = field(default_factory=now)


@dataclass
class AuditEntry:
    id: int
    actor: str
    node_id: int | None
    action: str
    detail: str
    ts: datetime = field(default_factory=now)


@dataclass
class User:
    id: int
    name: str
    email: str
    role: str              # Owner | Manager | Technician | Viewer


# Heartbeat window: telemetry older than this renders the node offline/stale.
HEARTBEAT_WINDOW = timedelta(seconds=120)
OVERRIDE_MAX = timedelta(minutes=30)

FIRMWARE = [
    FirmwareRelease("1.4.2", "Latest — adaptive rain timing + eco-mode fixes", is_latest=True),
    FirmwareRelease("1.4.0", "Power-aware OTA, RTC drift correction"),
    FirmwareRelease("1.3.5", "Initial fleet release"),
]


class Store:
    def __init__(self) -> None:
        self._ids = itertools.count(1000)
        n = now()
        self.org = Organization(1, "Riverside Public Works")
        self.users = [
            User(1, "Avery Chen", "avery@riverside.gov", "Owner"),
            User(2, "Sam Okafor", "sam@riverside.gov", "Manager"),
            User(3, "Dana Reyes", "dana@riverside.gov", "Technician"),
            User(4, "Stakeholder", "council@riverside.gov", "Viewer"),
        ]
        self.current_user = self.users[1]  # acting as Manager
        self.sites = [
            Site(1, 1, "Downtown Corridor", "Main St corridor"),
            Site(2, 1, "Riverside Campus", "Campus loop"),
        ]
        # Nodes — a small fleet with deliberately varied health states.
        self.nodes = [
            Node(1, "STN-0A1F", "Main & 1st", "Main St / 1st Ave", 1, "online",
                 34.0561, -117.1894, "1.4.2", True, n),
            Node(2, "STN-0A2C", "Main & 5th", "Main St / 5th Ave", 1, "online",
                 34.0578, -117.1860, "1.4.0", True, n - timedelta(seconds=20)),
            Node(3, "STN-0B07", "Main & Oak", "Main St / Oak Blvd", 1, "online",
                 34.0599, -117.1822, "1.4.0", True, n - timedelta(seconds=8)),
            Node(4, "STN-0C44", "Campus North", "Campus Loop / North Gate", 2, "offline",
                 34.0641, -117.1771, "1.3.5", True, n - timedelta(minutes=14)),
            Node(5, "STN-0C91", "Campus South", "Campus Loop / South Gate", 2, "online",
                 34.0610, -117.1748, "1.4.2", True, n - timedelta(seconds=35)),
            Node(6, "STN-0D12", "Bench unit", "Workshop bench", 2, "provisioning",
                 34.0625, -117.1790, "1.3.5", False, n - timedelta(minutes=2)),
        ]
        # One active plan per node (+ a staged draft on node 1).
        self.plans: list[TimingPlan] = []
        pid = itertools.count(1)
        for nd in self.nodes:
            self.plans.append(TimingPlan(
                next(pid), nd.id, 1, "Default day plan",
                red_s=30, amber_s=4, green_s=25,
                schedule="All day", adaptive_rules="Extend amber +2s when rain detected",
                active=True))
        self.plans.append(TimingPlan(
            next(pid), 1, 2, "Rush-hour plan (staged)",
            red_s=20, amber_s=4, green_s=40,
            schedule="Mon-Fri 07:00-09:30",
            adaptive_rules="Flash red below 5 lux", staged=True))
        # Alerts — varied lifecycle states.
        self.alerts = [
            Alert(1, 4, "offline", "critical", "Node missed 7 heartbeats (last seen 14 min ago)"),
            Alert(2, 5, "low_battery", "warning", "Battery 28% — may not survive the night"),
            Alert(3, 3, "solar", "warning", "Solar harvest 40% below 7-day average — panel likely soiled"),
            Alert(4, 2, "heat", "info", "Enclosure 51 C — within limits, trending up", state="acknowledged"),
            Alert(5, 1, "fault", "warning", "RTC drift 3.2s detected", state="resolved"),
        ]
        self.events: list[Event] = [
            Event(1, 1, "bringup", "Commissioning checklist PASSED (6/6)", now() - timedelta(days=40)),
            Event(2, 4, "fault", "LTE modem registration lost", now() - timedelta(minutes=14)),
            Event(3, 3, "diagnostic", "Full self-test: 5/6 PASS (solar low)", now() - timedelta(hours=3)),
        ]
        self.maintenance: list[MaintenanceRecord] = [
            MaintenanceRecord(1, 3, "Dana Reyes", "Cleaned panel, harvest recovered to 46W", now() - timedelta(days=12)),
        ]
        self.firmware = FIRMWARE
        self.ota_jobs: list[OtaJob] = []
        self.audit: list[AuditEntry] = [
            AuditEntry(1, "Sam Okafor", 1, "apply_plan", "Applied 'Default day plan' v1", now() - timedelta(days=40)),
            AuditEntry(2, "Dana Reyes", 3, "service_mode", "Entered service mode for panel cleaning", now() - timedelta(days=12)),
        ]

    # ── id helpers ──
    def next_id(self) -> int:
        return next(self._ids)

    # ── accessors ──
    def node(self, node_id: int) -> Node | None:
        return next((x for x in self.nodes if x.id == node_id), None)

    def site(self, site_id: int) -> Site | None:
        return next((x for x in self.sites if x.id == site_id), None)

    def site_name(self, site_id: int) -> str:
        s = self.site(site_id)
        return s.name if s else "—"

    def node_plans(self, node_id: int) -> list[TimingPlan]:
        return sorted([p for p in self.plans if p.node_id == node_id],
                      key=lambda p: p.version, reverse=True)

    def active_plan(self, node_id: int) -> TimingPlan | None:
        return next((p for p in self.node_plans(node_id) if p.active), None)

    def node_alerts(self, node_id: int, include_resolved: bool = False) -> list[Alert]:
        out = [a for a in self.alerts if a.node_id == node_id]
        if not include_resolved:
            out = [a for a in out if a.state != "resolved"]
        return out

    def open_alerts(self) -> list[Alert]:
        return [a for a in self.alerts if a.state in ("open", "acknowledged", "snoozed")]

    def node_events(self, node_id: int) -> list[Event]:
        return sorted([e for e in self.events if e.node_id == node_id],
                      key=lambda e: e.ts, reverse=True)

    def add_audit(self, action: str, detail: str, node_id: int | None = None) -> None:
        self.audit.append(AuditEntry(
            self.next_id(), self.current_user.name, node_id, action, detail))


# Module-level singleton — the running app's mock cloud.
db = Store()
