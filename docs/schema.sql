-- AltLens database schema (PostgreSQL)
--
-- This mirrors backend/altlens/models.py. Either create the tables with
-- `python -m altlens.seed_data`, which runs SQLAlchemy's create_all and loads
-- the illustrative dataset, or apply this file directly.
--
-- Design notes:
--   * asset_class on funds is the one field that makes expansion beyond
--     venture capital painless: private equity, real estate, and hedge fund
--     rows slot into the same tables.
--   * Cash flows are stored as discrete dated events rather than as start and
--     end values. Accurate IRR needs real cash-flow timing; storing only
--     beginning and ending NAV is the shortcut that produces wrong numbers.
--   * fund_metrics is a cache written by the calculation job, not a source of
--     truth. Recompute it from cash_flows whenever those change.
--   * source_references is the audit trail: every figure should be traceable
--     to a source, a confidence level, and a verified/estimated/illustrative
--     status.

CREATE TABLE IF NOT EXISTS funds (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    manager_name    VARCHAR(255),
    asset_class     VARCHAR(50)  NOT NULL DEFAULT 'venture_capital',
    vintage_year    INT,
    fund_size_usd   NUMERIC(18, 2),
    strategy        VARCHAR(255),
    geography       VARCHAR(100),
    description     TEXT,
    data_quality    VARCHAR(50)  NOT NULL DEFAULT 'illustrative',
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_funds_asset_class ON funds (asset_class);
CREATE INDEX IF NOT EXISTS idx_funds_vintage_year ON funds (vintage_year);

CREATE TABLE IF NOT EXISTS cash_flows (
    id          SERIAL PRIMARY KEY,
    fund_id     INT NOT NULL REFERENCES funds (id) ON DELETE CASCADE,
    event_date  DATE NOT NULL,
    -- Negative = capital call (outflow), positive = distribution (inflow).
    amount_usd  NUMERIC(18, 2) NOT NULL,
    flow_type   VARCHAR(50) NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cash_flows_fund_date
    ON cash_flows (fund_id, event_date);

CREATE TABLE IF NOT EXISTS performance_snapshots (
    id                           SERIAL PRIMARY KEY,
    fund_id                      INT NOT NULL REFERENCES funds (id) ON DELETE CASCADE,
    snapshot_date                DATE NOT NULL,
    nav_usd                      NUMERIC(18, 2),
    cumulative_distributions_usd NUMERIC(18, 2),
    created_at                   TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_snapshots_fund_date
    ON performance_snapshots (fund_id, snapshot_date);

CREATE TABLE IF NOT EXISTS portfolio_positions (
    id                SERIAL PRIMARY KEY,
    fund_id           INT NOT NULL REFERENCES funds (id) ON DELETE CASCADE,
    company_name      VARCHAR(255) NOT NULL,
    sector            VARCHAR(100),
    stage             VARCHAR(50),
    invested_usd      NUMERIC(18, 2),
    current_value_usd NUMERIC(18, 2),
    status            VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_positions_sector ON portfolio_positions (sector);

-- Computed metrics cache. IRR is stored as a decimal (0.24 = 24%).
CREATE TABLE IF NOT EXISTS fund_metrics (
    fund_id         INT PRIMARY KEY REFERENCES funds (id) ON DELETE CASCADE,
    irr             NUMERIC(12, 6),
    moic            NUMERIC(12, 4),
    tvpi            NUMERIC(12, 4),
    dpi             NUMERIC(12, 4),
    last_calculated TIMESTAMP NOT NULL DEFAULT NOW()
);

-- The source and assumption ledger.
CREATE TABLE IF NOT EXISTS source_references (
    id           SERIAL PRIMARY KEY,
    fund_id      INT REFERENCES funds (id) ON DELETE CASCADE,
    source_name  VARCHAR(255) NOT NULL,
    source_url   TEXT,
    field_name   VARCHAR(100),
    confidence   VARCHAR(50) NOT NULL DEFAULT 'low',
    -- 'verified' | 'estimated' | 'illustrative'
    data_status  VARCHAR(50) NOT NULL DEFAULT 'illustrative',
    notes        TEXT,
    observed_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sources_fund ON source_references (fund_id);

-- Post-MVP: cross-asset correlation once a second asset class exists.
-- CREATE TABLE asset_class_returns (
--     asset_class VARCHAR(50),
--     period_date DATE,
--     return_pct  NUMERIC,
--     PRIMARY KEY (asset_class, period_date)
-- );
