# AltLens Product Direction

AltLens should take inspiration from public-market research agents, but its advantage should be alternative-investment intelligence rather than a Bloomberg clone.

The goal is to build an AI-powered research workspace for venture capital and, later, other private-market asset classes. It should help users move from a broad research question to a verifiable investment brief with data tables, calculations, charts, citations, and transparent assumptions.

## Product Thesis

Most public-market agents focus on stocks, SEC filings, earnings, real-time prices, and news. AltLens can be more distinctive by focusing on the harder private-market workflow:

- fund and manager comparison
- vintage-year analysis
- cash-flow based performance metrics
- portfolio-company exposure
- sector and theme research
- diligence memo generation
- source-backed assumptions when perfect data is unavailable
- clear separation between verified data, illustrative demo data, and AI interpretation

The product should feel like a research analyst that can reason over messy private-market material, not just a chatbot over market data.

## Differentiators

### 1. Alternative-Investment Native

AltLens should center its data model around private-market concepts:

- funds
- managers
- vintage years
- asset classes
- cash flows
- NAV snapshots
- distributions
- portfolio companies
- sectors
- geographies
- deal stages
- valuation marks
- exit events

Public equities can be added later as context, but the core product should not be designed around stock tickers.

### 2. Verifiable Research Briefs

The main AI output should be a structured research brief, not just a conversational answer.

Each brief should include:

- executive summary
- key metrics
- supporting tables
- charts
- cited sources
- assumptions
- data quality notes
- follow-up questions

For a demo, this can begin as a deterministic template populated by backend tools. Later, the AI agent can assemble richer briefs from multiple tools.

### 3. Tool-Calling Agent With Guardrails

The AI layer should use fixed tools instead of unrestricted SQL generation.

Example tools:

- `get_fund_profile`
- `get_fund_metrics`
- `compare_funds`
- `get_top_performers`
- `get_vintage_year_summary`
- `get_sector_exposure`
- `generate_research_brief`
- `explain_metric_methodology`

The agent should never invent performance data. If data is illustrative, incomplete, or unavailable, the UI and response should say so directly.

### 4. Local And Cloud Model Support

AltLens should eventually support interchangeable model providers:

- OpenAI for strong hosted reasoning
- Ollama for local models
- future providers through a common model adapter

Local-model support is useful because finance workflows often involve sensitive research material. However, the first implementation should keep model routing simple:

1. define a provider interface
2. implement OpenAI first
3. add Ollama after the tool layer is stable

Smaller local models may struggle with multi-step financial tool use, so the product should expose model selection without assuming all models can handle all workflows.

### 5. Analysis Workspace

AltLens should include an analysis layer that can run safe, predefined quantitative workflows:

- IRR/MOIC recalculation
- vintage-year comparisons
- event-window analysis around exits or market shocks
- sector exposure summaries
- fund ranking and peer grouping
- chart-ready data transforms

Early versions should avoid arbitrary AI-generated code execution. A safer path is to build approved analysis functions first, then consider sandboxed code execution later if the project needs it.

### 6. Source And Assumption Ledger

Private-market data is often incomplete. AltLens should make this a feature, not a weakness.

Each generated brief should track:

- source name
- source URL or document reference when available
- field extracted
- confidence level
- whether the value is verified, estimated, or illustrative
- last updated date

This creates a research audit trail and makes the platform more credible for AIA use.

## Proposed Agent Workflow

1. User asks a research question.
2. Backend classifies the intent.
3. Agent chooses from approved tools.
4. Tools retrieve fund data, metrics, source notes, and chart-ready series.
5. Backend assembles a structured response.
6. Frontend displays the answer as a research brief with tables, charts, and citations.
7. User can drill into funds, sources, or assumptions.

## Example Prompts

- "Create a research brief comparing 2018 vintage VC funds in enterprise SaaS."
- "Which funds have the strongest MOIC but weak DPI?"
- "Compare Fund A and Fund B across IRR, MOIC, vintage year, and sector exposure."
- "Show the assumptions behind the IRR estimate for this fund."
- "Which portfolio companies drive the most exposure to AI infrastructure?"
- "Generate an AIA-style memo on late-stage VC performance since 2021."

## Development Sequence

### Near Term

1. Keep building the backend foundation.
2. Add database models for funds, cash flows, snapshots, and metrics.
3. Add seed data with clear `illustrative` flags.
4. Add API endpoints for fund list, fund detail, metrics, and top performers.
5. Add a dashboard that exposes the data before adding a complex agent.

### Middle Term

1. Add source tracking tables.
2. Add research-brief response models.
3. Add deterministic brief generation from existing backend tools.
4. Add the first AI route using constrained tool calling.
5. Add charts and source citations to the frontend.

### Later

1. Add local model support through Ollama.
2. Add provider switching through a model adapter.
3. Add document ingestion for PDFs, reports, and exported datasets.
4. Add sandboxed quantitative analysis only after core tools are stable.
5. Expand beyond VC into private equity, real estate, and hedge funds.

## Design Principle

AltLens should be powerful because it is trustworthy. Every impressive AI answer should be backed by inspectable data, explicit assumptions, and repeatable calculations.
