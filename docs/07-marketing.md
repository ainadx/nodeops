# Marketing Pack — NodeOps

*AiNa Build · Stage 7 (Marketing cluster) · 2026-06-20*

Synthesis of: Brand Strategist · Copywriter · Visual Designer → assembled into
`app/marketing.html` (open it in a browser). Brand aligned to the campaign:
**DKube purple + Poppins**.

## Positioning statement
For **field installers and small-city signal operators**, NodeOps is the
**phone-first companion** that takes a Smart Traffic Node from a box of parts to
years of unattended operation — guiding the build, running live bring-up tests,
and watching power, signal, and connectivity from the base of the pole —
**unlike the laptop + serial terminal + PDF + spreadsheet** it replaces.

## Target persona
- **Archetype:** "Dana, the field tech who commissions and services nodes."
- **JTBD:** bring a node up correctly and know instantly when a deployed one is
  in trouble.
- **Current workaround:** a laptop, a serial terminal, a PDF assembly guide, a
  BOM spreadsheet, and two JSON connection maps — and a drive-by to find a dead
  node.
- **Pain:** no single place; outages discovered by accident; bring-up needs a
  bench.
- **Decision trigger:** the second node — or the first 2 a.m. blackout nobody saw.

## Brand voice
- **Grounded** — speaks the hardware's language (I²C, SSR, SoC), not buzzwords.
- **Safety-first** — calm, exact, never hypes control. "Refused: needs a live link."
- **Field-ready** — short, scannable, works one-handed at a pole.

## Tagline (3 variants → primary)
1. **"From bench to boulevard."** ← primary
2. "Every node, in your pocket."
3. "Build it. Watch it. Keep it alive."

## Anti-positioning
- Not a city-wide traffic-optimization AI (that's the later corridor phase).
- Not a closed proprietary ITS stack — open hardware, self-hostable.
- Not a consumer/driver app — it's for the people who run the nodes.

## Messaging pillars (one per P0 capability)
- **Provision** — Scan, pair, confirm cloud check-in before you leave site.
- **Bring up** — I²C scan, sensor + SSR + rail self-tests over BLE; a
  commissioning gate that won't let a half-tested node go live.
- **Operate** — Live signal, battery runtime, solar, cellular, RTC — one health
  verdict at a glance, with guardrailed timing-plan control.
- **Maintain** — A map that pages you the moment a node drops, plus OTA, audit,
  and energy forecasting.

## Visual system (applied in marketing.html)
| Role | Hex |
|---|---|
| Primary (DKube purple) | `#6D28D9` |
| Primary deep | `#4C1D95` |
| Accent (signal green) | `#12B76A` |
| Text | `#0F1117` · Muted `#5B6472` |
| Background | `#FFFFFF` · Alt `#F6F4FF` (purple-tint) |
| Warning `#F79009` · Danger `#F04438` |

- **Type:** Poppins (headings 600/700, body 400/500) via Google Fonts.
- **Layout:** centered hero on a purple-tinted gradient; 4-up feature grid;
  `<details>` FAQ; copy-paste social cards; max-width 1100px.
- **Components:** pill CTAs (purple, rounded-full), soft cards
  (`rounded-2xl border shadow-sm`), letter-glyph signal badges echoing the app.

## FAQ (in the page)
- Do I need the hardware to try it? — No; the console runs against a mock fleet.
- Is it safe to control signals from a phone? — Control is confirmed,
  time-bounded, logged, and refused without a live link; the node fails safe on
  its own.
- One node or a hundred? — Both; a maker single-node mode and a city fleet view,
  one app.
- Open source? — The hardware and firmware are open; bring your own cloud.

## Social posts (in the page)
- **X/Twitter:** "Your solar traffic node shouldn't be a mystery box. NodeOps:
  scan, bring-up self-tests, live power+signal, alerts that page you. From bench
  to boulevard. 🚦"
- **LinkedIn:** "Small cities run real signals on open hardware. NodeOps gives
  installers and operators one phone-first place to provision, monitor, and
  safely control them — with an audit log for every change."
- **Maker forum:** "Built a Smart Traffic Node? Skip the laptop + serial
  terminal. Run the I²C scan and SSR test from your phone over BLE, then watch
  battery + solar from anywhere."
