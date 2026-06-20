"""P0 acceptance tests for the NodeOps console.

Each test maps to a PRD §Features acceptance criterion and asserts what an
operator/integration observes through the HTTP surface.
"""
from datetime import timedelta


# P0 — Provisioning: register -> provisioning; check-in blocked until commissioned
def test_provisioning_and_checkin_gate(client):
    r = client.post("/nodes", data={"serial": "STN-TEST", "name": "Test node",
                                     "intersection": "A / B", "site_id": 1})
    assert r.status_code == 200
    # New node id is the highest; fetch the fleet JSON to find it
    nodes = client.get("/api/nodes").json()["nodes"]
    new = next(n for n in nodes if n["serial"] == "STN-TEST")
    assert new["status"] == "provisioning"
    # Check-in is refused until commissioning passes (fail-safe gate)
    r = client.post(f"/nodes/{new['id']}/checkin")
    assert "Cannot go online" in r.headers.get("x-toast", "")


# P0 — Bring-up: I2C scan on a healthy node lists all documented sensors
def test_bringup_i2c_detects_all_sensors(client):
    body = client.post("/nodes/1/bringup/i2c").text   # node 1 is healthy
    assert "BME280" in body and "BH1750" in body and "DS3231" in body
    assert "PASS" in body


# P0 — Bring-up: a wiring fault surfaces as FAIL (bench node), and commissioning
# cannot pass until the required tests pass.
def test_bringup_failure_path_and_commission_gate(client):
    nid = 6  # seeded bench node with a deliberate I2C fault
    body = client.post(f"/nodes/{nid}/bringup/i2c").text
    assert "FAIL" in body and "NOT DETECTED" in body
    # commission cannot pass while a required test is failing
    r = client.post(f"/nodes/{nid}/bringup/commission")
    assert "FAIL" in r.headers.get("x-toast", "")


# P0 — Single-node dashboard: offline node renders stale, not live
def test_offline_node_renders_stale(client):
    r = client.get("/nodes/4/telemetry")   # node 4 is seeded offline
    assert r.status_code == 200
    assert "offline" in r.text.lower() or "stale" in r.text.lower()


# P0 — Timing plans are versioned: editing creates a new version, old retained
def test_plan_edit_creates_new_version(client):
    r = client.post("/nodes/1/plan", data={"name": "Tuned", "red_s": 22,
                    "amber_s": 4, "green_s": 28, "apply_now": "apply"})
    assert r.status_code == 200
    page = client.get("/nodes/1/control").text
    assert "v2" in page and "v1" in page          # both versions retained
    assert "Tuned" in page


# P0 — Control safety: applying a plan to an offline node is refused
def test_control_refused_when_offline(client):
    r = client.post("/nodes/4/plan", data={"name": "X", "red_s": 20,
                    "amber_s": 4, "green_s": 20, "apply_now": "apply"})
    assert "Refused" in r.headers.get("x-toast", "")


# P0 — Manual override is time-bounded and recorded with an expiry
def test_override_is_time_bounded_and_audited(client):
    r = client.post("/nodes/1/override", data={"phase": "all_red", "minutes": 5})
    assert "auto-expires" in r.headers.get("x-toast", "")
    from app import store
    n = store.db.node(1)
    assert n.override_expires_at is not None
    assert n.override_expires_at - store.now() <= timedelta(minutes=5, seconds=1)
    # audited
    assert any(e.action == "override" for e in store.db.audit)


# P0 — Override is clamped to the 30-min ceiling
def test_override_clamped_to_ceiling(client):
    client.post("/nodes/1/override", data={"phase": "green", "minutes": 999})
    from app import store
    n = store.db.node(1)
    assert n.override_expires_at - store.now() <= timedelta(minutes=30, seconds=1)


# P0 — Alert lifecycle: open -> acknowledged -> resolved
def test_alert_lifecycle(client):
    r = client.post("/alerts/1/ack")
    assert "acknowledged" in r.text
    r = client.post("/alerts/1/resolve")
    assert "resolved" in r.text


# P0 — Fleet filter + search
def test_fleet_search_and_filter(client):
    r = client.get("/fleet", params={"q": "STN-0C44"})
    assert "Campus North" in r.text
    r = client.get("/fleet", params={"status": "offline"})
    assert "Campus North" in r.text       # the offline node
    assert "Main & 1st" not in r.text     # an online node filtered out


# P0 — RBAC/audit: control actions land in the append-only audit log
def test_audit_log_records_control(client):
    client.post("/nodes/1/override", data={"phase": "all_red", "minutes": 2})
    page = client.get("/audit").text
    assert "override" in page


# P1 — OTA is power-aware: low battery defers the update
def test_ota_power_aware_defer(client):
    # node 5 is seeded at 28% SoC -> must defer
    r = client.post("/firmware/5/update")
    assert "deferred" in r.headers.get("x-toast", "").lower()


# Smoke: every primary page renders 200
def test_all_pages_render(client):
    for p in ["/", "/fleet", "/map", "/nodes/1", "/nodes/1/control",
              "/nodes/6/bringup", "/alerts", "/audit", "/firmware",
              "/roadmap", "/healthz", "/api/nodes"]:
        assert client.get(p).status_code == 200, p
