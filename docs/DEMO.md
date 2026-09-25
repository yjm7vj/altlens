# AltLens demo script

Fifteen minutes, two terminals, no API key and no database required.

## Before you start

```bash
uvicorn altlens.main:app --reload --app-dir backend
```

```bash
cd frontend && npm run dev
```

Open http://localhost:5173. Confirm the J-curve renders and the fund table
lists ten funds. If `/api` calls fail, the backend is on a different port —
set `VITE_PROXY_TARGET` in `frontend/.env.local`.

## The opening line

Say this early, not defensively:

> This is seeded with illustrative data. The architecture is built to plug in
> licensed sources like PitchBook or Preqin once the club has access — and
> every figure on screen tells you it's illustrative, which is the point.

That framing is stronger than presenting synthetic numbers as verified ones,
and it sets up the provenance markers.

## Walkthrough

**1. The J-curve (30 seconds).** Capital called against capital returned, with
break-even marked in June 2025. This is the shape that separates private
markets from public ones: money leaves for years before any comes back. A
public-market dashboard has nothing to show here.

**2. The fund table (1 minute).** Ten funds, sortable. Point at the DPI and
RVPI columns: teal is cash already returned, ochre is value still marked on
paper. Lattice Early Stage II sits at 0.00x DPI and 1.29x RVPI — a young fund
whose whole return is still unrealized. Note that it still has an IRR, because
AltLens treats remaining NAV as a terminal distribution.

**3. A fund detail (1 minute).** Click Frontier Seed Partners II. Metrics,
its own J-curve, portfolio companies, every cash-flow event, and the source
ledger underneath. Every figure traces to something.

**4. The research panel (5 minutes).** Work through the questions below.

## The five demo questions

Run these before any live demo. Each has been verified to produce a
tool-backed answer.

| Question | Tool it should call | What to point out |
|---|---|---|
| What's the IRR for Frontier Seed Partners II? | `get_fund_metrics` | 21.4% IRR, and the paid-in / distributed / NAV figures behind it. |
| Which fund had the best performance? | `get_top_performers` | Ranked by IRR, with the full metric set per fund. |
| Compare AltLens Ventures I and Summit Growth VC III | `compare_funds` | 2.68x versus 1.42x, and the DPI gap underneath. |
| What is the average MOIC across all funds? | `get_top_performers` | The average is computed by the backend, not written by the model. |
| How did hedge funds perform last year? | *none* | **The important one.** It refuses. No tool fits, so there is no answer. |

Two more worth having ready:

- *Create a research brief on 2018 vintage funds* — returns a full structured
  brief: summary, metric table, assumptions, reasons to doubt it, sources,
  and follow-up questions you can click.
- *How is IRR calculated?* — the methodology note, including the caveat that
  the figure depends on unaudited NAV marks.

## The three things to land

1. **The agent cannot invent a number.** Open `/api/ai/tools` in a browser tab
   if anyone asks. Those nine functions are everything it can reach. It picks
   one; the backend calculates; the model only phrases the result.
2. **The refusal is a feature.** Ask the hedge-fund question deliberately.
   A research tool that says "I don't have that" is worth more than one that
   produces a plausible paragraph.
3. **Provenance is built in, not bolted on.** Every figure carries a marker,
   every brief carries its assumptions and its reasons to doubt it. When real
   data arrives, the same ledger shows what's verified and what isn't.

## If something breaks

- Charts blank: the backend is down or on another port. Check
  http://127.0.0.1:8000/api/health.
- The agent answers oddly: it is running the deterministic router, which is
  keyword-based by design. Fall back to the five verified questions.
- A model provider fails mid-demo: AltLens falls back to rule-based routing
  automatically and says so in the data-quality notes. Nothing goes blank.
