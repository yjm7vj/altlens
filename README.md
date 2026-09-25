# AltLens

AI-powered research workspace for alternative investments, built for the
Alternative Investments Association (AIA).

AltLens centralizes private-market fund data, computes cash-flow based
performance metrics, and answers research questions through a constrained
agent that can only call approved backend tools. The MVP covers venture
capital, on a schema designed so private equity, real estate, and hedge funds
slot in without a redesign.

See [BUILD_PLAN.md](BUILD_PLAN.md) for the architecture plan,
[PRODUCT_DIRECTION.md](PRODUCT_DIRECTION.md) for the product thesis, and
[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) for the build history.

> **All data in this repository is illustrative.** The seeded figures are
> synthetic, generated to exercise the platform. They are not verified fund
> performance and are not investment advice. The ingestion layer is built so
> licensed sources (PitchBook, Preqin, Cambridge Associates) can replace them
> without touching the schema or the API.

## What it does

- **Cash-flow based metrics.** XIRR-style IRR, MOIC, DPI, RVPI and TVPI,
  computed from dated capital calls and distributions rather than from
  beginning and ending NAV.
- **The J-curve.** Cumulative capital called against capital returned across
  the portfolio, with the break-even crossover marked.
- **Fund exploration.** Sortable fund table, per-fund cash flows, portfolio
  companies, sector concentration, and vintage-year cohorts.
- **A constrained research agent.** Ask a question in plain English; the agent
  picks from nine approved tools, and the UI shows which tools ran before it
  shows the answer. It never writes SQL and never produces a figure itself.
- **Structured research briefs.** Summary, metric tables, assumptions,
  data-quality caveats, source ledger, and follow-up questions.
- **A source and assumption ledger.** Every figure carries a provenance
  marker: verified, estimated, or illustrative.

## Quick start

Two terminals. Neither step needs a database or an API key.

**Backend**

```bash
python -m venv .venv
```

```bash
.venv\Scripts\Activate.ps1
```

```bash
python -m pip install -e ".[dev]"
```

```bash
uvicorn altlens.main:app --reload --app-dir backend
```

The API comes up on http://127.0.0.1:8000, with interactive docs at
http://127.0.0.1:8000/docs.

**Frontend**

```bash
cd frontend && npm install && npm run dev
```

The dashboard is at http://localhost:5173. Vite proxies `/api` to the backend;
if port 8000 is taken, set `VITE_PROXY_TARGET` in `frontend/.env.local`.

**Tests**

```bash
python -m pytest
```

## Architecture

```
React + Vite dashboard  ──▶  FastAPI  ──▶  analytics layer  ──▶  demo dataset
      (Recharts)                 │                                (or Postgres)
                                 ▼
                        research agent
                     provider picks a tool
                     AltLens runs the tool
                     provider narrates the result
```

The agent is deliberately narrow. A model never sees the database and never
generates a query — it chooses one of the tools in `ai_tools.py`, AltLens runs
it, and the model only phrases the result. When no tool fits the question, the
answer is a refusal rather than a guess.

### Repository layout

```
backend/altlens/
  metrics.py      IRR, MOIC, DPI, RVPI, TVPI
  demo_data.py    the illustrative dataset
  analytics.py    approved analysis functions over that dataset
  research.py     deterministic research-brief assembly
  ai_tools.py     the fixed tool registry the agent may call
  providers.py    rule-based, OpenAI, and Ollama adapters
  ai_agent.py     plan, run tools, narrate, with guardrails
  main.py         FastAPI routes
  models.py       SQLAlchemy models
  database.py     async engine and session scope
  seed_data.py    loads the demo dataset into Postgres
frontend/src/
  components/     dashboard, charts, fund detail, research panel
  api/client.js   fetch wrapper
docs/schema.sql   raw SQL for the full schema
tests/            71 tests across metrics, analytics, agent, and API
```

## Model providers

| Provider | Setup | Notes |
|---|---|---|
| `rule_based` | none | Default. Deterministic keyword routing, always available, works offline. |
| `openai` | `OPENAI_API_KEY` | Tool calling restricted to the approved tools. |
| `ollama` | a running Ollama server | For sensitive material. Small local models often fail to pick a tool, so AltLens falls back to rule-based routing rather than answering with unbacked prose. |

Set `ALTLENS_MODEL_PROVIDER`, or pass `provider` per request to
`/api/ai/query`. See [.env.example](.env.example) for every setting.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Status, fund count, data-source disclaimer |
| GET | `/api/funds` | Fund list, filterable by vintage, strategy, manager |
| GET | `/api/funds/with-metrics` | Fund list joined with computed metrics |
| GET | `/api/funds/{id}` | Full detail: metrics, cash flows, holdings, sources |
| GET | `/api/funds/{id}/performance` | NAV and distribution time series |
| GET | `/api/funds/{id}/metrics` | Metrics for one fund |
| GET | `/api/funds/{id}/sources` | Source ledger for one fund |
| GET | `/api/metrics/top` | Top funds by irr, moic, tvpi, dpi, or rvpi |
| GET | `/api/metrics/vintages` | Vintage-year cohorts with median IRR and MOIC |
| GET | `/api/metrics/sectors` | Sector exposure by portfolio-company value |
| GET | `/api/metrics/capital-timeline` | The J-curve, portfolio-wide or per fund |
| GET | `/api/metrics/methodology/{metric}` | How a metric is calculated, and its caveats |
| GET | `/api/sources` | The full source ledger |
| POST | `/api/research/brief` | Deterministic structured brief |
| POST | `/api/ai/query` | Natural-language question, tool-backed answer |
| GET | `/api/ai/tools` | Every tool the agent may call |
| GET | `/api/ai/providers` | Which model providers are configured |

## Using a database

The API does not need one. To exercise the same data against Postgres:

```bash
python -m altlens.seed_data --reset
```

Set `ALTLENS_DATABASE_URL` first. `postgres://` and `postgresql://` URLs are
rewritten to the async driver automatically. The raw DDL is in
[docs/schema.sql](docs/schema.sql).

## Deployment

- Backend: [render.yaml](render.yaml) is a working Render blueprint. Delete
  the `databases` block to deploy the demo with no Postgres.
- Frontend: [frontend/vercel.json](frontend/vercel.json). Set
  `VITE_API_BASE_URL` to the deployed API origin, and add the frontend origin
  to `ALTLENS_CORS_ORIGINS` on the backend.

## Status

Feature-complete against the build plan: metrics, schema, seed data, REST API,
dashboard, charts, source tracking, research briefs, the constrained AI query
endpoint, local and cloud model providers, and deployment config. The
remaining work is data, not code — replacing the illustrative dataset with
licensed sources.
