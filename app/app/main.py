"""NodeOps Console — FastAPI + HTMX operator surface for Smart Traffic Nodes.

This is the reference Cloud<->App seam from the PRD, rendered server-side on the
golden design system. It talks to two mocks (`store.py` = mock cloud,
`sim.py` = mock device/BLE) so the entire product — provisioning, bring-up,
monitoring, guardrailed control, fleet map, alerts, OTA, audit — is demoable
without hardware. The production iOS/Android clients consume the same routes.

Run locally:  uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .sim import health_verdict, is_fresh, run_bringup_test, snapshot
from .store import OVERRIDE_MAX, Alert, Event, OtaJob, TimingPlan, db, now

APP_NAME = os.environ.get("APP_NAME", "NodeOps")
APP_TAGLINE = os.environ.get("APP_TAGLINE", "One companion for the whole life of a Smart Traffic Node.")
REPO_URL = os.environ.get("NEXT_PUBLIC_REPO_URL", "https://github.com/your-org/nodeops")

BASE_DIR = Path(__file__).resolve().parent.parent
app = FastAPI(title=APP_NAME)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _toast(html: str, message: str, status_code: int = 200) -> HTMLResponse:
    """HTMX fragment + a toast in the X-Toast header (must stay ASCII-safe)."""
    safe = (message or "").encode("ascii", "replace").decode("ascii")
    return HTMLResponse(html, status_code=status_code, headers={"X-Toast": safe})


_ICONS = {
    "grid": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/></svg>',
    "list": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><circle cx="3.5" cy="6" r="1.2"/><circle cx="3.5" cy="12" r="1.2"/><circle cx="3.5" cy="18" r="1.2"/></svg>',
    "map": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M9 3 4 5v16l5-2 6 2 5-2V3l-5 2-6-2Z"/><line x1="9" y1="3" x2="9" y2="19"/><line x1="15" y1="5" x2="15" y2="21"/></svg>',
    "bell": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></svg>',
    "chip": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/></svg>',
    "log": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M14 3v4a1 1 0 0 0 1 1h4"/><path d="M17 21H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2Z"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="13" y2="17"/></svg>',
    "fw": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/></svg>',
}

NAV = [
    {"key": "dashboard", "label": "Overview", "href": "/", "icon": _ICONS["grid"]},
    {"key": "fleet", "label": "Fleet", "href": "/fleet", "icon": _ICONS["list"]},
    {"key": "map", "label": "Map", "href": "/map", "icon": _ICONS["map"]},
    {"key": "alerts", "label": "Alerts", "href": "/alerts", "icon": _ICONS["bell"]},
    {"key": "firmware", "label": "Firmware (OTA)", "href": "/firmware", "icon": _ICONS["fw"]},
    {"key": "audit", "label": "Audit log", "href": "/audit", "icon": _ICONS["log"]},
    {"key": "roadmap", "label": "Roadmap", "href": "/roadmap", "icon": _ICONS["chip"]},
]

PHASE_META = {
    "red": ("R", "#f04438", "Red"),
    "amber": ("A", "#f79009", "Amber"),
    "green": ("G", "#12b76a", "Green"),
    "flashing_red": ("FR", "#f04438", "Flashing red"),
    "all_red": ("AR", "#f04438", "All red"),
    "dark": ("—", "#667085", "Dark / no signal"),
}


def ctx(request: Request, active: str, **extra):
    return {
        "request": request, "app_name": APP_NAME, "app_tagline": APP_TAGLINE,
        "repo_url": REPO_URL, "nav": NAV, "active": active,
        "user": db.current_user, "phase_meta": PHASE_META, **extra,
    }


def _fleet_kpis() -> dict:
    total = len(db.nodes)
    online = sum(1 for n in db.nodes if is_fresh(n))
    on_batt = sum(1 for n in db.nodes if is_fresh(n) and snapshot(n).solar_w < 2)
    open_alerts = len(db.open_alerts())
    uptime = round(100 * online / total, 1) if total else 0
    return {"total": total, "online": online, "offline": total - online,
            "on_batt": on_batt, "open_alerts": open_alerts, "uptime": uptime}


def _node_view(n) -> dict:
    """The denormalised per-node row the list/map/dashboard all share."""
    key, label, badge = health_verdict(n)
    snap = snapshot(n)
    phase = PHASE_META.get(snap.signal_phase, PHASE_META["dark"])
    age = int((now() - n.last_seen).total_seconds())
    return {"node": n, "verdict_key": key, "verdict_label": label, "verdict_badge": badge,
            "snap": snap, "phase": phase, "site": db.site_name(n.site_id), "age_s": age}


# ── Overview ──────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    views = [_node_view(n) for n in db.nodes]
    at_risk = [v for v in views if v["verdict_key"] in ("critical", "offline", "attention")]
    alerts = sorted(db.open_alerts(), key=lambda a: a.created_at, reverse=True)[:5]
    return templates.TemplateResponse(request, "pages/dashboard.html", ctx(
        request, "dashboard", kpis=_fleet_kpis(), at_risk=at_risk, alerts=alerts,
        node_name={n.id: n.name for n in db.nodes}))


# ── Fleet list ─────────────────────────────────────────────────────────────
@app.get("/fleet", response_class=HTMLResponse)
def fleet(request: Request, status: str = "all", site: str = "all", q: str = ""):
    views = [_node_view(n) for n in db.nodes]
    if status != "all":
        views = [v for v in views if v["verdict_key"] == status]
    if site != "all":
        views = [v for v in views if str(v["node"].site_id) == site]
    if q:
        ql = q.lower()
        views = [v for v in views if ql in v["node"].name.lower()
                 or ql in v["node"].serial.lower() or ql in v["node"].intersection.lower()]
    body = templates.get_template("partials/node_rows.html").render(ctx(request, "fleet", views=views))
    if request.headers.get("HX-Request"):
        return HTMLResponse(body)
    return templates.TemplateResponse(request, "pages/fleet.html", ctx(
        request, "fleet", views=views, sites=db.sites, status=status, site=site, q=q,
        rows_html=body))


# ── Map ────────────────────────────────────────────────────────────────────
@app.get("/map", response_class=HTMLResponse)
def fleet_map(request: Request):
    views = [_node_view(n) for n in db.nodes]
    lats = [n.lat for n in db.nodes]
    lons = [n.lon for n in db.nodes]
    lat0, lat1 = min(lats), max(lats)
    lon0, lon1 = min(lons), max(lons)

    def xy(n):
        x = 8 + 84 * (n.lon - lon0) / (lon1 - lon0 or 1)
        y = 92 - 84 * (n.lat - lat0) / (lat1 - lat0 or 1)
        return round(x, 2), round(y, 2)
    pins = []
    color = {"good": "#12b76a", "attention": "#f79009", "critical": "#f04438",
             "offline": "#f04438", "setup": "#667085"}
    for v in views:
        x, y = xy(v["node"])
        pins.append({**v, "x": x, "y": y, "color": color.get(v["verdict_key"], "#667085")})
    return templates.TemplateResponse(request, "pages/map.html", ctx(
        request, "map", pins=pins, kpis=_fleet_kpis()))


# ── Single node ────────────────────────────────────────────────────────────
@app.get("/nodes/{node_id}", response_class=HTMLResponse)
def node_detail(request: Request, node_id: int):
    n = db.node(node_id)
    if not n:
        return PlainTextResponse("Node not found", status_code=404)
    v = _node_view(n)
    plan = db.active_plan(node_id)
    alerts = db.node_alerts(node_id, include_resolved=True)
    return templates.TemplateResponse(request, "pages/node.html", ctx(
        request, "fleet", v=v, plan=plan, alerts=alerts,
        events=db.node_events(node_id)[:6],
        override_active=v["snap"].overridden,
        override_left=_override_left(n)))


def _override_left(n) -> int:
    if n.override_expires_at and n.override_expires_at > now():
        return int((n.override_expires_at - now()).total_seconds())
    return 0


@app.get("/nodes/{node_id}/telemetry", response_class=HTMLResponse)
def node_telemetry(request: Request, node_id: int):
    """HTMX-polled live telemetry fragment for the single-node dashboard."""
    n = db.node(node_id)
    if not n:
        return PlainTextResponse("", status_code=404)
    v = _node_view(n)
    return templates.TemplateResponse(request, "partials/telemetry.html", ctx(
        request, "fleet", v=v, override_left=_override_left(n)))


# ── Provisioning ───────────────────────────────────────────────────────────
@app.post("/nodes", response_class=HTMLResponse)
def add_node(request: Request, serial: str = Form(...), name: str = Form(...),
             intersection: str = Form(""), site_id: int = Form(1)):
    from .store import Node
    nid = db.next_id()
    nd = Node(nid, serial.strip().upper() or f"STN-{nid}", name.strip() or "New node",
              intersection.strip() or "Unassigned", site_id, "provisioning",
              34.062, -117.178, "1.3.5", False, now())
    db.nodes.append(nd)
    db.plans.append(TimingPlan(db.next_id(), nid, 1, "Default day plan",
                               30, 4, 25, "All day", "—", active=True))
    db.add_audit("add_node", f"Registered {nd.serial} ({nd.name})", nid)
    html = f'<tr><td colspan="6"><a class="btn btn--primary btn--sm" href="/nodes/{nid}/bringup">Start bring-up for {nd.serial} -></a></td></tr>'
    return _toast(html, f"Node {nd.serial} registered - start bring-up")


@app.post("/nodes/{node_id}/checkin", response_class=HTMLResponse)
def checkin(request: Request, node_id: int):
    n = db.node(node_id)
    if not n:
        return PlainTextResponse("", status_code=404)
    if not n.commissioned:
        return _toast("", "Cannot go online - commissioning checklist not passed", 200)
    n.status = "online"
    n.last_seen = now()
    db.add_audit("checkin", f"{n.serial} confirmed cloud check-in", node_id)
    return _toast(
        f'<span class="badge badge--success">online</span>',
        f"{n.serial} is online - provisioning confirmed")


# ── Bring-up wizard ────────────────────────────────────────────────────────
@app.get("/nodes/{node_id}/bringup", response_class=HTMLResponse)
def bringup_page(request: Request, node_id: int):
    n = db.node(node_id)
    if not n:
        return PlainTextResponse("Node not found", status_code=404)
    tests = [("i2c", "I2C bus scan"), ("sensors", "Sensor self-test"),
             ("ssr", "SSR output test"), ("rails", "DC rail verification")]
    return templates.TemplateResponse(request, "pages/bringup.html", ctx(
        request, "fleet", n=n, tests=tests, results=n.bringup))


@app.post("/nodes/{node_id}/bringup/{test}", response_class=HTMLResponse)
def bringup_test(request: Request, node_id: int, test: str):
    n = db.node(node_id)
    if not n:
        return PlainTextResponse("", status_code=404)
    res = run_bringup_test(n, test)
    if test != "commission":
        n.bringup[test] = {"pass": res["pass"], "detail": res["detail"],
                           "ts": now().isoformat()}
    else:
        if res["pass"]:
            n.commissioned = True
            db.events.append(Event(db.next_id(), node_id, "bringup",
                                   "Commissioning checklist PASSED"))
            db.add_audit("commission", f"{n.serial} commissioning PASSED", node_id)
    html = templates.get_template("partials/bringup_result.html").render(
        ctx(request, "fleet", test=test, res=res, n=n))
    return _toast(html, f"{res['title']}: {'PASS' if res['pass'] else 'FAIL'}")


# ── Signal control: timing plans + override ────────────────────────────────
@app.get("/nodes/{node_id}/control", response_class=HTMLResponse)
def control_page(request: Request, node_id: int):
    n = db.node(node_id)
    if not n:
        return PlainTextResponse("Node not found", status_code=404)
    return templates.TemplateResponse(request, "pages/control.html", ctx(
        request, "fleet", n=n, plans=db.node_plans(node_id),
        plan_active=db.active_plan(node_id), fresh=is_fresh(n),
        override_left=_override_left(n)))


@app.post("/nodes/{node_id}/plan", response_class=HTMLResponse)
def save_plan(request: Request, node_id: int, name: str = Form(...),
              red_s: int = Form(...), amber_s: int = Form(...), green_s: int = Form(...),
              schedule: str = Form("All day"), adaptive_rules: str = Form("—"),
              apply_now: str = Form("stage")):
    n = db.node(node_id)
    if not n:
        return PlainTextResponse("", status_code=404)
    # Editing always creates a NEW version (old versions retained).
    ver = max((p.version for p in db.node_plans(node_id)), default=0) + 1
    plan = TimingPlan(db.next_id(), node_id, ver, name.strip() or f"Plan v{ver}",
                      max(1, red_s), max(1, amber_s), max(1, green_s),
                      schedule, adaptive_rules,
                      created_by=db.current_user.name)
    if apply_now == "apply":
        if not is_fresh(n):
            return _toast("", "Refused: cannot apply a plan to an offline node (fail-safe)", 200)
        for p in db.node_plans(node_id):
            p.active = False
        plan.active = True
        db.add_audit("apply_plan", f"Applied '{plan.name}' v{ver} ({red_s}/{amber_s}/{green_s}s)", node_id)
        msg = f"Applied '{plan.name}' v{ver}"
    else:
        plan.staged = True
        db.add_audit("stage_plan", f"Staged '{plan.name}' v{ver}", node_id)
        msg = f"Staged '{plan.name}' v{ver} (not live)"
    db.plans.append(plan)
    rows = templates.get_template("partials/plan_versions.html").render(
        ctx(request, "fleet", plans=db.node_plans(node_id)))
    return _toast(rows, msg)


@app.post("/nodes/{node_id}/plan/{plan_id}/apply", response_class=HTMLResponse)
def apply_staged(request: Request, node_id: int, plan_id: int):
    n = db.node(node_id)
    plan = next((p for p in db.plans if p.id == plan_id and p.node_id == node_id), None)
    if not n or not plan:
        return PlainTextResponse("", status_code=404)
    if not is_fresh(n):
        return _toast("", "Refused: node offline - fail-safe blocks remote control", 200)
    for p in db.node_plans(node_id):
        p.active = False
    plan.active = True
    plan.staged = False
    db.add_audit("apply_plan", f"Applied staged '{plan.name}' v{plan.version}", node_id)
    rows = templates.get_template("partials/plan_versions.html").render(
        ctx(request, "fleet", plans=db.node_plans(node_id)))
    return _toast(rows, f"Applied '{plan.name}' v{plan.version}")


@app.post("/nodes/{node_id}/override", response_class=HTMLResponse)
def override(request: Request, node_id: int, phase: str = Form(...),
             minutes: int = Form(5)):
    n = db.node(node_id)
    if not n:
        return PlainTextResponse("", status_code=404)
    if not is_fresh(n):
        return _toast("", "Refused: manual override needs a live link", 200)
    mins = max(1, min(minutes, int(OVERRIDE_MAX.total_seconds() // 60)))
    n.override_phase = phase
    n.override_expires_at = now() + timedelta(minutes=mins)
    n.override_by = db.current_user.name
    db.add_audit("override", f"Manual override -> {phase.upper()} for {mins} min (auto-expires)", node_id)
    html = f'<span class="badge badge--danger">OVERRIDE {phase.upper()} - expires in {mins}:00</span>'
    return _toast(html, f"Override {phase.upper()} active for {mins} min - auto-expires")


@app.post("/nodes/{node_id}/override/clear", response_class=HTMLResponse)
def clear_override(request: Request, node_id: int):
    n = db.node(node_id)
    if not n:
        return PlainTextResponse("", status_code=404)
    n.override_phase = None
    n.override_expires_at = None
    db.add_audit("override_clear", "Cleared manual override - restored scheduled plan", node_id)
    return _toast('<span class="badge badge--success">scheduled plan restored</span>',
                  "Override cleared - scheduled plan restored")


# ── Service mode (maintenance) ─────────────────────────────────────────────
@app.post("/nodes/{node_id}/service", response_class=HTMLResponse)
def toggle_service(request: Request, node_id: int):
    n = db.node(node_id)
    if not n:
        return PlainTextResponse("", status_code=404)
    if n.status == "maintenance":
        n.status = "online"
        n.last_seen = now()
        db.add_audit("service_exit", "Exited service mode - signal restored", node_id)
        msg = "Service mode ended - signal restored"
        badge = '<span class="badge badge--success">online</span>'
    else:
        n.status = "maintenance"
        db.events.append(Event(db.next_id(), node_id, "service", "Entered service mode (safe state)"))
        db.add_audit("service_mode", "Entered service mode (all-red safe state)", node_id)
        msg = "Service mode ON - signal in safe state"
        badge = '<span class="badge badge--warning">service mode</span>'
    return _toast(badge, msg)


# ── Alerts ─────────────────────────────────────────────────────────────────
@app.get("/alerts", response_class=HTMLResponse)
def alerts_page(request: Request, state: str = "active"):
    items = db.alerts
    if state == "active":
        items = [a for a in items if a.state != "resolved"]
    elif state in ("open", "acknowledged", "snoozed", "resolved"):
        items = [a for a in items if a.state == state]
    items = sorted(items, key=lambda a: (a.severity != "critical", a.created_at), reverse=False)
    name = {n.id: n.name for n in db.nodes}
    return templates.TemplateResponse(request, "pages/alerts.html", ctx(
        request, "alerts", alerts=items, node_name=name, state=state))


@app.post("/alerts/{alert_id}/{action}", response_class=HTMLResponse)
def alert_action(request: Request, alert_id: int, action: str):
    a = next((x for x in db.alerts if x.id == alert_id), None)
    if not a:
        return PlainTextResponse("", status_code=404)
    if action == "ack":
        a.state = "acknowledged"
    elif action == "snooze":
        a.state = "snoozed"
        a.snoozed_until = now() + timedelta(hours=2)
    elif action == "resolve":
        a.state = "resolved"
    db.add_audit(f"alert_{action}", f"{a.kind} alert {action} on node {a.node_id}", a.node_id)
    name = {n.id: n.name for n in db.nodes}
    html = templates.get_template("partials/alert_row.html").render(
        ctx(request, "alerts", a=a, node_name=name))
    return _toast(html, f"Alert {action} - {a.kind}")


# ── Firmware / OTA ─────────────────────────────────────────────────────────
@app.get("/firmware", response_class=HTMLResponse)
def firmware_page(request: Request):
    latest = next((f for f in db.firmware if f.is_latest), db.firmware[0])
    rows = []
    for n in db.nodes:
        snap = snapshot(n)
        behind = n.firmware != latest.version
        rows.append({"node": n, "behind": behind, "soc": snap.battery_soc,
                     "can_update": behind and n.status != "offline"})
    return templates.TemplateResponse(request, "pages/firmware.html", ctx(
        request, "firmware", rows=rows, latest=latest, releases=db.firmware,
        jobs=sorted(db.ota_jobs, key=lambda j: j.ts, reverse=True)))


@app.post("/firmware/{node_id}/update", response_class=HTMLResponse)
def ota_update(request: Request, node_id: int):
    n = db.node(node_id)
    latest = next((f for f in db.firmware if f.is_latest), db.firmware[0])
    if not n:
        return PlainTextResponse("", status_code=404)
    if n.status == "offline":
        return _toast("", "Cannot update an offline node", 200)
    snap = snapshot(n)
    if snap.battery_soc < 50:
        job = OtaJob(db.next_id(), node_id, latest.version, "deferred",
                     f"Battery {snap.battery_soc}% < 50% - power-aware defer")
        db.ota_jobs.append(job)
        db.add_audit("ota_defer", f"OTA to {latest.version} deferred (battery {snap.battery_soc}%)", node_id)
        return _toast(f'<span class="badge badge--warning">deferred (battery {snap.battery_soc}%)</span>',
                      "OTA deferred - battery below 50% (power-aware)")
    prev = n.firmware
    n.firmware = latest.version
    job = OtaJob(db.next_id(), node_id, latest.version, "done", f"From {prev}")
    db.ota_jobs.append(job)
    db.add_audit("ota_apply", f"OTA {prev} -> {latest.version}", node_id)
    return _toast(f'<span class="badge badge--success">{latest.version}</span>',
                  f"Updated {n.serial} to {latest.version}")


@app.post("/firmware/{node_id}/rollback", response_class=HTMLResponse)
def ota_rollback(request: Request, node_id: int):
    n = db.node(node_id)
    if not n:
        return PlainTextResponse("", status_code=404)
    prev = next((f.version for f in db.firmware if not f.is_latest), n.firmware)
    old = n.firmware
    n.firmware = prev
    db.ota_jobs.append(OtaJob(db.next_id(), node_id, prev, "rolled_back", f"From {old}"))
    db.add_audit("ota_rollback", f"Rolled back {old} -> {prev}", node_id)
    return _toast(f'<span class="badge">{prev}</span>', f"Rolled back {n.serial} to {prev}")


# ── Audit ──────────────────────────────────────────────────────────────────
@app.get("/audit", response_class=HTMLResponse)
def audit_page(request: Request):
    entries = sorted(db.audit, key=lambda e: e.ts, reverse=True)
    name = {n.id: n.name for n in db.nodes}
    return templates.TemplateResponse(request, "pages/audit.html", ctx(
        request, "audit", entries=entries, node_name=name))


# ── Roadmap + health + JSON mirror ─────────────────────────────────────────
ROADMAP = [
    {"title": "Provisioning, bring-up self-tests & commissioning", "state": "done", "note": "P0 - shipped"},
    {"title": "Single-node monitoring + fleet map/list/alerts", "state": "done", "note": "P0 - shipped"},
    {"title": "Versioned timing plans + guardrailed override", "state": "done", "note": "P0 - shipped"},
    {"title": "OTA (canary, power-aware, rollback) + RBAC + maintenance", "state": "progress", "note": "P1 - in progress"},
    {"title": "Energy intelligence (runtime forecast, eco mode)", "state": "planned", "note": "P2"},
    {"title": "Reporting, integrations & corridor green-wave", "state": "planned", "note": "P2 / stretch"},
]


@app.get("/roadmap", response_class=HTMLResponse)
def roadmap_page(request: Request):
    return templates.TemplateResponse(request, "pages/roadmap.html",
                                      ctx(request, "roadmap", roadmap=ROADMAP))


@app.get("/api/nodes")
def api_nodes():
    """Thin JSON mirror of the fleet (what the mobile client / integrations call)."""
    out = []
    for n in db.nodes:
        snap = snapshot(n)
        key, label, _ = health_verdict(n)
        out.append({"id": n.id, "serial": n.serial, "name": n.name,
                    "status": n.status, "health": key, "signal": snap.signal_phase,
                    "battery_soc": snap.battery_soc, "runtime_hrs": snap.runtime_hrs,
                    "solar_w": snap.solar_w, "last_seen": n.last_seen.isoformat()})
    return JSONResponse({"org": db.org.name, "nodes": out})


@app.get("/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"
