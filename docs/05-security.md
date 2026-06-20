# Security Review — NodeOps

*AiNa Build · Stage 5 (Security cluster) · 2026-06-20*

Synthesis of: Threat Modeler · Dependency Auditor · Code Scanner · Synthesizer.
NodeOps controls **public road infrastructure**, so security and safety are the
same conversation: a spoofed command is a physical hazard.

## Threat model (STRIDE, prioritised)

| Threat | Vector | Impact | Mitigation |
|---|---|---|---|
| **Spoofed signal command** | Forged Cloud→Device or App→Cloud message | Dangerous signal state | Per-device keys + **mutual TLS**; signed, idempotent, **time-bounded** commands; node **fail-safe** rejects invalid/stale commands and reverts to all-red |
| **Stolen/lost phone** | Cached session controls a fleet | Unauthorized control | Biometric app lock; short session TTL; **instant server-side revocation**; control re-confirmed per action |
| **Privilege escalation** | Viewer/Tech issues control | Unauthorized change | **Server-side RBAC** (never trust client); control routes gated by role; optional **two-person approval** for fleet-wide actions |
| **Tampering with OTA** | Malicious firmware image | Bricked/again-hostile node | **Signed** images, canary rollout, resumable, **rollback**, power-aware defer |
| **Replay / stale apply** | Re-send an old plan/override | Wrong timing reinstated | Idempotency keys + monotonic version on TimingPlan; node ignores out-of-order/expired commands |
| **Tamper / theft** | Enclosure opened, node moved | Hardware loss / safety | Tamper + motion alerts; audit + last-known location |
| **Info disclosure** | Telemetry/location leak | Privacy of asset map | TLS in transit; scope data to org; minimal PII (accounts only) |
| **Repudiation** | "I didn't change that" | Accountability gap | **Append-only audit log** of every control/config/access action |
| **DoS / data exhaustion** | Flood telemetry, blow SIM cap | Cost + blind fleet | Tunable cadence; SIM usage caps + alerts; broker rate limits |

### Trust boundaries
1. App ↔ Cloud (REST/WS) — authenticated user session + RBAC.
2. Cloud ↔ Device (MQTT) — mutual TLS, per-device identity.
3. App ↔ Device (BLE) — local pairing; provisioning only, no live signal control.
**The node is the final authority on its own signal** — never trusts app/cloud
for safety.

## Control-safety invariants (must hold in every client)
- Every state-changing signal action is **confirmed, idempotent, time-bounded,
  logged**.
- **Manual overrides expire** automatically and auto-restore the scheduled plan.
- Control is **refused without a live link** (verified in `test_control_refused_when_offline`).
- Loss of command link / invalid plan / watchdog → node reverts to last-known-good
  or all-red, independent of app & cloud.

## Dependency audit (reference build)
`fastapi`, `uvicorn[standard]`, `jinja2`, `python-multipart` — all current,
pinned, no known CVEs at build time. No client-side JS supply chain beyond
**vendored** HTMX (no CDN). Action: enable Dependabot + `pip-audit` in CI;
pin a lockfile for prod.

## Code scan findings (reference build)
- **No raw SQL / no DB** in the reference build → no injection surface; Jinja
  autoescaping on by default (XSS-safe). When Postgres lands, use parameterized
  queries / an ORM only.
- **`X-Toast` header** is forced ASCII via `_toast()` — prevents a header-
  injection / 500 class of bug.
- **No secrets in code**; config via env (`.env` gitignored).
- **Gap (expected for V0):** no auth/session yet, RBAC modeled not enforced,
  `current_user` fixed. These are P1 — see readiness doc. Do **not** expose this
  reference build to the public internet with control routes live.

## Top recommendations (ranked)
1. Implement **server-side auth + RBAC enforcement** before any real device is
   reachable (P1, blocking for production).
2. Stand up **mutual-TLS device identity** + signed commands on the MQTT seam.
3. Add **two-person approval** for fleet-wide override/OTA.
4. CI: `pip-audit`, Dependabot, secret scanning, a lockfile.
5. Penetration test the three seams against the replay/spoof cases above before
   a city pilot.

**Verdict:** the V0 reference build is safe to run locally/in staging; the
control-safety invariants are correctly modeled and tested. Auth/RBAC/mTLS are
the non-negotiable gates before any production node is controllable.
