# AltLens

AI-powered analytics platform for alternative investments research, built for the Alternative Investments Association (AIA).

This repository is being developed gradually. The current focus is a venture-capital MVP with:

- reliable fund performance metrics
- a FastAPI backend
- a React dashboard
- a constrained AI research agent that calls approved backend tools
- structured, source-backed research briefs

See [BUILD_PLAN.md](BUILD_PLAN.md) for the full product and architecture plan.
See [PRODUCT_DIRECTION.md](PRODUCT_DIRECTION.md) for the larger AI research-agent vision.

## Development Roadmap

The project will be built in small commits over the month:

1. Backend foundation and tested metric calculations
2. Database models and seed data
3. REST endpoints for funds, performance, and metrics
4. Frontend dashboard shell
5. Charts and fund exploration views
6. Source and assumption tracking
7. Research brief generation
8. AI query endpoint with constrained tools
9. Local/cloud model provider options
10. Demo polish, deployment config, and documentation

## Backend Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```

## Current Status

Day-one foundation: metric calculations and tests.
