# CLAUDE.md — NodeOps agent operating context

Operating instructions for the next AI coding agent. Derived from `docs/` (the
intended-state baseline) and `POST_LAUNCH_PHASE1.md` (the backlog). Read those
for the *why*; this file is the *what may and may not be touched*.

## What this is
The **reference operator console** for Smart Traffic Nodes — the Cloud↔App seam
rendered server-side (FastAPI + HTMX) against two in-process mocks. It is the
test harness and reference implementation for the production mobile clients +
node firmware, **not** the shipping mobile binary.

- `app/app/store.py` — **mock cloud**: entity graph + seeded fleet (in-memory).
- `app/app/sim.py` — **mock device/BLE**: deterministic telemetry + bring-up tests.
- `app/app/main.py` — FastAPI routes (HTMX fragments + `/api/*` JSON mirror).
- `app/templates/`, `app/static/` — Jinja pages + design system.
- `app/tests/` — 13 P0 acceptance tests. **Keep them green.**

## Trust boundaries & guardrails (do not weaken)
1. **Signal-control safety is the product.** Any change to control flow resolves
   to the *safest* option. Every state-changing signal action must stay
   **confirmed, idempotent, time-bounded, and audit-logged**.
2. **Control is refused on an offline node** (`is_fresh()` gate). Never remove
   this; the node fails safe on its own in production.
3. **Manual overrides must auto-expire** (`OVERRIDE_MAX`, clamped). Never make an
   override open-ended.
4. **Audit log is append-only.** Do not add edit/delete routes for `AuditEntry`.
5. **HTTP headers must be ASCII** — build toasts only through `_toast()`.
6. **Editing a timing plan creates a new version** — never mutate an existing
   version in place (staging/copy/rollback depend on this).
7. Health/signal indicators carry **letter + shape** cues, not color alone (a11y).

## Known gaps (intended — see POST_LAUNCH_PHASE1.md)
- **No auth / RBAC enforcement yet** — `db.current_user` is fixed. Feature 1 is
  the blocking gate before any real node is controllable. Do NOT expose this
  build to the public internet with control routes live.
- Persistence is in-memory (resets). Real device seam is mocked.

## How to work here
- Run: `cd app && uvicorn app.main:app --reload --port 8000`
- Test: `cd app && pytest -q` (must stay 13/13).
- Add domain UI by **extending** the design system classes — never fork
  `static/css/app.css` or re-emit `base.html`.
- New work should attach to the highest existing seam (store/sim/main), not
  invent a new one.
