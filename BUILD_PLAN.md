# AltLens — Build Plan

**AI-powered analytics platform for alternative investments research**
Built for the Alternative Investments Association (AIA)

---

## 1. Project Overview

### 1.1 Problem
AIA's sector research process is currently manual — pulling data from scattered sources, calculating fund performance metrics by hand, and building one-off visualizations for each research cycle. There's no shared, persistent tool that lets members explore performance data interactively.

### 1.2 Solution
AltLens is a full-stack web application that centralizes alternative investment performance data, computes standard performance metrics (IRR, MOIC), visualizes fund and sector performance, and lets members query the data in plain English via an AI-powered search layer.

### 1.3 MVP Scope Decision
Building all four asset classes (PE, hedge funds, real estate, VC) with live data integration and a fully general natural-language query engine in 1-2 weeks is not realistic. This plan scopes the MVP to:

- **One asset class for launch: Venture Capital.** VC has the most accessible public/illustrative data (deal announcements, public reporting from well-known funds, Crunchbase-style data points) compared to PE and hedge funds, which are largely behind paywalls (PitchBook, Preqin, HFR).
- **A schema designed for expansion.** Adding PE, real estate, and hedge funds later should mean adding rows and a few asset-class-specific fields, not redesigning the database.
- **A constrained AI search layer.** Rather than open-ended natural language to SQL (fragile, risky on financial data), the AI layer uses a fixed set of tools/functions the LLM can call. This is safer, more demoable, and easier to extend.

### 1.4 Tech Stack
| Layer | Technology | Why |
|---|---|---|
| Frontend | React + Vite, Tailwind CSS, Recharts | Fast dev loop, matches existing AIA dashboard stack |
| Backend | FastAPI (Python) | Async support, automatic OpenAPI docs, fast to build REST endpoints |
| Database | PostgreSQL | Relational structure fits fund/performance data well; supports future scale |
| AI Layer | OpenAI API + LangChain | Tool-calling support for constrained, safe NL queries |
| Hosting | Vercel (frontend), Render or Railway (backend + DB) | Free/cheap tiers sufficient for a club demo |

---

## 2. System Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   React Frontend │ ──────▶ │   FastAPI Backend │ ──────▶ │   PostgreSQL     │
│  (Dashboard, AI   │ ◀────── │  (REST + AI route) │ ◀────── │  (Funds, Metrics) │
│   Search Bar)     │         │                    │         │                  │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                      │
                                      ▼
                              ┌──────────────────┐
                              │  LangChain Agent   │
                              │  + OpenAI API      │
                              │  (Tool-calling)    │
                              └──────────────────┘
```

**Request flow for AI search:**
1. User types a question in plain English (e.g., "Which fund had the highest IRR in 2022?")
2. Frontend sends the question to `/api/ai/query`
3. Backend invokes a LangChain agent with access to a fixed set of tools (e.g., `get_fund_performance`, `compare_funds`, `get_top_performers`)
4. The agent selects the right tool(s), the tool queries Postgres, and the agent formats a natural-language answer
5. Response returned to frontend and displayed in the search UI

---

## 3. Database Schema

### 3.1 Core Tables

```sql
-- Funds table: one row per fund/entity being tracked
CREATE TABLE funds (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    asset_class VARCHAR(50) NOT NULL DEFAULT 'venture_capital', -- future: 'private_equity', 'hedge_fund', 'real_estate'
    vintage_year INT,                  -- year fund was raised
    fund_size_usd NUMERIC,             -- total committed capital
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Cash flow events: capital calls and distributions (needed for accurate IRR)
CREATE TABLE cash_flows (
    id SERIAL PRIMARY KEY,
    fund_id INT REFERENCES funds(id) ON DELETE CASCADE,
    event_date DATE NOT NULL,
    amount_usd NUMERIC NOT NULL,       -- negative = capital call (outflow), positive = distribution (inflow)
    flow_type VARCHAR(50) NOT NULL,    -- 'capital_call', 'distribution'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance snapshots: periodic valuation data for time-series charts
CREATE TABLE performance_snapshots (
    id SERIAL PRIMARY KEY,
    fund_id INT REFERENCES funds(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    nav_usd NUMERIC,                   -- net asset value at this point in time
    cumulative_distributions_usd NUMERIC,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Computed metrics cache: avoid recalculating IRR/MOIC on every request
CREATE TABLE fund_metrics (
    fund_id INT PRIMARY KEY REFERENCES funds(id) ON DELETE CASCADE,
    irr NUMERIC,                       -- internal rate of return (decimal, e.g., 0.24 = 24%)
    moic NUMERIC,                      -- multiple on invested capital
    tvpi NUMERIC,                      -- total value to paid-in (future enhancement)
    last_calculated TIMESTAMP DEFAULT NOW()
);
```

### 3.2 Schema Design Notes
- `asset_class` on the `funds` table is the single field that makes future expansion painless — PE/real estate/hedge fund rows slot into the same table.
- Cash flows are modeled as discrete events (not just start/end values) because **accurate IRR requires actual cash flow timing**, not just beginning and ending NAV. This is the single most common shortcut that produces wrong IRR numbers — don't skip it.
- `fund_metrics` is a cache table populated by the backend's calculation job, not computed live on every page load.

### 3.3 Future Schema Extensions (post-MVP)
```sql
-- For cross-asset correlation, once 2+ asset classes exist:
CREATE TABLE asset_class_returns (
    asset_class VARCHAR(50),
    period_date DATE,
    return_pct NUMERIC,
    PRIMARY KEY (asset_class, period_date)
);
```

---

## 4. Metric Calculations

### 4.1 MOIC (Multiple on Invested Capital)
Straightforward: total value returned divided by total capital invested.

```python
def calculate_moic(cash_flows: list[dict]) -> float:
    """
    cash_flows: list of {amount_usd, flow_type}
    Returns MOIC as a float (e.g., 2.3 means 2.3x capital returned)
    """
    invested = sum(abs(cf["amount_usd"]) for cf in cash_flows if cf["flow_type"] == "capital_call")
    returned = sum(cf["amount_usd"] for cf in cash_flows if cf["flow_type"] == "distribution")
    if invested == 0:
        return 0.0
    return returned / invested
```

### 4.2 IRR (Internal Rate of Return)
IRR requires solving for the discount rate that makes the net present value of all cash flows equal zero. Use `numpy-financial` or `scipy.optimize` rather than implementing Newton's method from scratch.

```python
import numpy_financial as npf
from datetime import date

def calculate_irr(cash_flows: list[dict]) -> float:
    """
    cash_flows: list of {event_date, amount_usd}, sorted chronologically
    Uses XIRR-style logic to handle irregular intervals between cash flows.
    """
    if len(cash_flows) < 2:
        return 0.0

    sorted_flows = sorted(cash_flows, key=lambda cf: cf["event_date"])
    base_date = sorted_flows[0]["event_date"]

    # Convert irregular dates into year-fractions for XIRR-style calculation
    years = [(cf["event_date"] - base_date).days / 365.0 for cf in sorted_flows]
    amounts = [cf["amount_usd"] for cf in sorted_flows]

    # XIRR via Newton's method (numpy_financial.irr assumes even periods, so we
    # implement XIRR manually for irregular real-world fund cash flow timing)
    from scipy.optimize import brentq

    def npv(rate):
        return sum(amt / (1 + rate) ** yr for amt, yr in zip(amounts, years))

    try:
        return brentq(npv, -0.99, 10)  # search between -99% and 1000% return
    except ValueError:
        return 0.0  # no solution found in range (e.g., all cash flows same sign)
```

**Validate this against known examples before trusting it** — test with a simple fund where you know the answer (e.g., invest $100 at year 0, receive $200 at year 5 should give ~14.9% IRR).

### 4.3 Testing Strategy
Write unit tests with at least 3 known cases:
1. Simple 2-cash-flow case (manually verifiable)
2. A fund with multiple capital calls over time
3. An edge case: a fund that lost money (negative IRR)

---

## 5. Backend API Design

### 5.1 Endpoint List

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/funds` | List all funds (with filters: asset_class, vintage_year) |
| GET | `/api/funds/{id}` | Get full detail for one fund, including metrics |
| GET | `/api/funds/{id}/performance` | Time-series NAV/distribution data for charting |
| GET | `/api/funds/{id}/metrics` | IRR, MOIC for one fund |
| GET | `/api/metrics/top` | Top N funds by IRR or MOIC |
| POST | `/api/ai/query` | Natural-language question → AI-generated answer |

### 5.2 Example FastAPI Skeleton

```python
# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AltLens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # update for deployed frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

class FundOut(BaseModel):
    id: int
    name: str
    asset_class: str
    vintage_year: int | None
    fund_size_usd: float | None
    irr: float | None
    moic: float | None

@app.get("/api/funds", response_model=list[FundOut])
def list_funds(asset_class: str | None = None):
    # query Postgres, join funds + fund_metrics, filter by asset_class if provided
    ...

@app.get("/api/funds/{fund_id}/performance")
def fund_performance(fund_id: int):
    # return time-series snapshots for charting
    ...

class AIQueryRequest(BaseModel):
    question: str

@app.post("/api/ai/query")
def ai_query(req: AIQueryRequest):
    # invoke LangChain agent — see Section 6
    ...
```

### 5.3 Database Access
Use SQLAlchemy with async support (`asyncpg` driver) for clean queries:

```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/altlens"
engine = create_async_engine(DATABASE_URL)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

---

## 6. AI Search Layer

### 6.1 Design Philosophy
Do **not** let the LLM generate raw SQL against the production database. Risks: incorrect queries, SQL injection-adjacent failure modes, no guardrails on what gets exposed. Instead, define a fixed set of "tools" (functions) the LLM can call. The LLM's job is to pick the right tool and parameters from the user's question — not to write database queries itself.

### 6.2 Tool Definitions

```python
# ai_tools.py
from langchain.tools import tool

@tool
def get_fund_performance(fund_name: str) -> str:
    """Get IRR, MOIC, and vintage year for a specific fund by name."""
    # look up fund in DB, return formatted string
    ...

@tool
def get_top_performers(asset_class: str = "venture_capital", metric: str = "irr", limit: int = 5) -> str:
    """Get the top N funds by IRR or MOIC within an asset class."""
    ...

@tool
def compare_funds(fund_names: list[str]) -> str:
    """Compare IRR and MOIC across 2+ named funds."""
    ...
```

### 6.3 Agent Setup

```python
# ai_agent.py
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from ai_tools import get_fund_performance, get_top_performers, compare_funds

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
tools = [get_fund_performance, get_top_performers, compare_funds]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are AltLens AI, a research assistant for alternative investment "
                "performance data. Only answer using the provided tools. If you don't "
                "have data to answer a question, say so clearly rather than guessing."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def run_query(question: str) -> str:
    result = agent_executor.invoke({"input": question})
    return result["output"]
```

### 6.4 Demo Reliability
Before any live demo, write down 5 example questions and verify they reliably produce good answers:
1. "What's the IRR for [specific fund name]?"
2. "Which fund had the best performance?"
3. "Compare [Fund A] and [Fund B]"
4. "What's the average MOIC across all funds?"
5. A deliberately out-of-scope question (e.g., about hedge funds, when only VC data exists) — the agent should say it doesn't have that data, not hallucinate an answer.

---

## 7. Frontend Structure

### 7.1 Component Tree

```
src/
├── App.jsx
├── components/
│   ├── Dashboard.jsx           # main layout, holds all dashboard widgets
│   ├── FundList.jsx            # table/grid of all funds with sort/filter
│   ├── FundDetail.jsx          # single fund deep-dive view
│   ├── PerformanceChart.jsx    # NAV over time, Recharts line chart
│   ├── MetricComparisonChart.jsx  # bar chart comparing IRR/MOIC across funds
│   ├── AISearchBar.jsx         # the natural-language query input + response display
│   └── TopPerformersWidget.jsx # leaderboard widget
├── api/
│   └── client.js               # fetch wrapper for backend calls
└── styles/
```

### 7.2 AI Search Bar Component (sketch)

```jsx
// AISearchBar.jsx
import { useState } from "react";

function AISearchBar() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    setLoading(true);
    const res = await fetch("/api/ai/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();
    setAnswer(data.answer);
    setLoading(false);
  }

  return (
    <div className="ai-search-bar">
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask about fund performance..."
        onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
      />
      <button onClick={handleSubmit} disabled={loading}>
        {loading ? "Thinking..." : "Ask"}
      </button>
      {answer && <div className="ai-answer">{answer}</div>}
    </div>
  );
}

export default AISearchBar;
```

### 7.3 Charting Notes
- Use Recharts for the performance line chart and bar comparisons — lighter weight than D3 for standard chart types and faster to ship.
- NAV-over-time chart: one line per fund, toggle-able via a legend.
- Keep the color palette consistent with AIA's existing branding if they have one.

---

## 8. Data Sourcing Plan (Critical Path)

This is the actual bottleneck of the project — code is straightforward, defensible data is not.

### 8.1 For the Demo
Use a small, hand-curated dataset of 8-12 well-known VC funds with **illustrative, approximately accurate** performance figures, clearly labeled as illustrative/demo data in the UI footer. Sources for directionally accurate figures: public reporting (TechCrunch, PitchBook's free published rankings/articles, fund LP letters that have been made public), Crunchbase's free tier for fund/deal metadata (not performance).

**Be upfront about this in the demo**: "This is seeded with illustrative data based on public reporting — the architecture is built to plug in licensed data sources (PitchBook, Preqin) once the club has access." This is a stronger pitch than presenting placeholder numbers as if they were verified.

### 8.2 Post-MVP
If AIA has or can get access to a paid data provider (PitchBook, Preqin, Cambridge Associates), the ingestion layer should be a separate module (`data_ingestion/`) so swapping in real data sources doesn't touch the core schema or API.

---

## 9. Build Timeline (14 Days)

| Days | Milestone |
|---|---|
| 1 | Finalize schema, set up Postgres locally, scaffold FastAPI + React repos |
| 2-3 | Curate demo dataset (8-12 VC funds + cash flow events), write seed script |
| 3-4 | Implement and unit-test IRR/MOIC calculation functions |
| 4-6 | Build core API endpoints (`/funds`, `/funds/{id}`, `/performance`, `/metrics/top`) |
| 5-8 | Build frontend dashboard: fund list, fund detail, performance chart (overlap with backend) |
| 8-10 | Build LangChain tools + agent, wire up `/api/ai/query` |
| 10-11 | Connect AI search bar in frontend, test against the 5 demo questions |
| 11-12 | Top performers widget, polish dashboard styling |
| 12-13 | Deploy frontend (Vercel) + backend/DB (Render/Railway) |
| 13-14 | Demo rehearsal, fix rough edges, prep talking points |

### 9.1 If Time Runs Short — Cut In This Order
1. Drop the AI agent's `compare_funds` tool, keep only the two simplest tools
2. Skip deployment, run the demo locally
3. Reduce demo dataset from 12 funds to 6
4. Replace the NAV-over-time chart with a static bar chart only (skip time-series if data isn't ready)

---

## 10. Repository Structure

```
altlens/
├── README.md
├── BUILD_PLAN.md              # this document
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py              # SQLAlchemy models
│   ├── schemas.py             # Pydantic schemas
│   ├── metrics.py             # IRR/MOIC calculation functions
│   ├── ai_tools.py
│   ├── ai_agent.py
│   ├── seed_data.py           # script to populate demo dataset
│   ├── requirements.txt
│   └── tests/
│       └── test_metrics.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   └── api/
│   ├── package.json
│   └── vite.config.js
└── docs/
    └── schema.sql              # raw SQL for full schema setup
```

---

## 11. Risks & Open Questions

| Risk | Mitigation |
|---|---|
| No access to licensed fund performance data | Use clearly-labeled illustrative data for the demo; design ingestion layer to swap in real sources later |
| IRR calculation edge cases (funds with no distributions yet, single cash flow) | Return null/N/A rather than crashing; add explicit unit tests for these cases |
| LLM agent gives a wrong or hallucinated answer live in front of AIA members | Restrict to tool-calling only (no freeform SQL generation), test the fixed question set repeatedly before the demo |
| 14-day timeline is aggressive | Timeline includes an explicit cut list (Section 9.1); scope to VC-only is the single biggest time-saver |
| Schema doesn't generalize cleanly to PE/real estate/hedge funds later | `asset_class` field and asset-class-agnostic core tables were designed with this in mind from day one |

---

## 12. Post-Demo Roadmap (If AIA Wants to Continue)

1. Add a second asset class (private equity is the natural next step — similar cash-flow-based metrics)
2. Cross-asset correlation matrix and heatmap visualization
3. User accounts so AIA members can save/annotate research
4. Real data provider integration (requires AIA budget discussion)
5. Export to PDF/PowerPoint for research reports (ties directly into the "double as a technical showcase" goal)
