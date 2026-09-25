import { useEffect, useMemo, useState } from "react";

import CapitalTimeline from "./CapitalTimeline";
import FundDetail from "./FundDetail";
import FundTable from "./FundTable";
import MetricComparisonChart from "./MetricComparisonChart";
import ResearchPanel from "./ResearchPanel";
import SectorExposure from "./SectorExposure";
import TopPerformersWidget from "./TopPerformersWidget";
import VintageChart from "./VintageChart";
import { DataStatusLegend } from "./DataStatus";
import { api } from "../api/client";
import { formatUsd } from "../format";

export default function Dashboard() {
  const [funds, setFunds] = useState([]);
  const [timeline, setTimeline] = useState(null);
  const [vintages, setVintages] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [selectedFundId, setSelectedFundId] = useState(null);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    Promise.all([
      api.fundsWithMetrics(),
      fetch("/api/metrics/capital-timeline").then((response) => response.json()),
      api.vintages(),
      api.sectors(),
    ])
      .then(([fundRows, capitalTimeline, vintageRows, sectorRows]) => {
        setFunds(fundRows);
        setTimeline(capitalTimeline);
        setVintages(vintageRows);
        setSectors(sectorRows);
      })
      .catch((problem) => setLoadError(problem.message));
  }, []);

  const totals = useMemo(() => {
    if (!funds.length) return null;

    const paidIn = funds.reduce(
      (sum, row) => sum + Number(row.metrics.paid_in_usd ?? 0),
      0,
    );
    const distributed = funds.reduce(
      (sum, row) => sum + Number(row.metrics.distributed_usd ?? 0),
      0,
    );
    const nav = funds.reduce(
      (sum, row) => sum + Number(row.metrics.residual_value_usd ?? 0),
      0,
    );

    return { paidIn, distributed, nav, count: funds.length };
  }, [funds]);

  if (loadError) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-16">
        <h1 className="text-lg font-semibold">AltLens can't reach the API</h1>
        <p className="mt-2 text-sm text-muted">{loadError}</p>
        <p className="mt-4 text-sm">
          Start the backend with{" "}
          <code className="bg-surface px-1">uvicorn altlens.main:app --reload</code>{" "}
          and reload this page.
        </p>
      </main>
    );
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-rule bg-surface">
        <div className="mx-auto flex max-w-[1400px] flex-wrap items-baseline justify-between gap-x-6 gap-y-2 px-4 py-4 sm:px-6">
          <div className="flex items-baseline gap-3">
            <h1 className="text-lg font-semibold tracking-tight">AltLens</h1>
            <p className="text-sm text-muted">
              Private-market fund research for the Alternative Investments
              Association
            </p>
          </div>
          <DataStatusLegend />
        </div>
      </header>

      <main className="mx-auto max-w-[1400px] px-4 py-6 sm:px-6">
        <section className="panel p-5" aria-labelledby="jcurve-heading">
          <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
            <div>
              <h2 id="jcurve-heading" className="text-base font-semibold">
                Capital called and returned
              </h2>
              <p className="mt-0.5 max-w-[60ch] text-sm text-muted">
                Money leaves the fund for years before any of it comes back.
                This is the shape a public-market dashboard can't show you.
              </p>
            </div>
            {totals ? (
              <dl className="flex flex-wrap gap-x-8 gap-y-2">
                <div>
                  <dt className="field-label">Called</dt>
                  <dd className="figure text-lg tabular-nums text-called">
                    {formatUsd(totals.paidIn)}
                  </dd>
                </div>
                <div>
                  <dt className="field-label">Returned in cash</dt>
                  <dd className="figure text-lg tabular-nums text-realized">
                    {formatUsd(totals.distributed)}
                  </dd>
                </div>
                <div>
                  <dt className="field-label">Still held at NAV</dt>
                  <dd className="figure text-lg tabular-nums text-unrealized">
                    {formatUsd(totals.nav)}
                  </dd>
                </div>
                <div>
                  <dt className="field-label">Funds tracked</dt>
                  <dd className="figure text-lg tabular-nums">{totals.count}</dd>
                </div>
              </dl>
            ) : null}
          </div>

          <div className="mt-4">
            <CapitalTimeline timeline={timeline} />
          </div>
        </section>

        <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
          <div className="min-w-0 space-y-6">
            <section className="panel p-5" aria-labelledby="funds-heading">
              <h2 id="funds-heading" className="text-sm font-semibold">
                Funds
              </h2>
              <p className="mt-0.5 text-micro text-muted">
                Select a fund to open its cash flows, holdings, and sources.
              </p>
              <div className="mt-3">
                <FundTable
                  rows={funds}
                  selectedFundId={selectedFundId}
                  onSelect={setSelectedFundId}
                />
              </div>
            </section>

            {selectedFundId ? (
              <FundDetail
                fundId={selectedFundId}
                onClose={() => setSelectedFundId(null)}
              />
            ) : null}

            <section className="panel p-5" aria-labelledby="realization-heading">
              <h2 id="realization-heading" className="text-sm font-semibold">
                What's been returned, what's still on paper
              </h2>
              <p className="mt-0.5 max-w-[60ch] text-micro text-muted">
                Two funds can share a MOIC and be nothing alike. The teal
                portion is cash already back with investors.
              </p>
              <div className="mt-3">
                <MetricComparisonChart funds={funds} height={Math.max(260, funds.length * 32)} />
              </div>
            </section>
          </div>

          <div className="min-w-0 space-y-6">
            <ResearchPanel />
            <TopPerformersWidget onSelect={setSelectedFundId} />

            <section className="panel p-5" aria-labelledby="vintage-heading">
              <h2 id="vintage-heading" className="text-sm font-semibold">
                By vintage year
              </h2>
              <div className="mt-3">
                <VintageChart vintages={vintages} />
              </div>
            </section>

            <section className="panel p-5" aria-labelledby="sector-heading">
              <h2 id="sector-heading" className="text-sm font-semibold">
                Sector concentration
              </h2>
              <div className="mt-3">
                <SectorExposure exposures={sectors} />
              </div>
            </section>
          </div>
        </div>
      </main>

      <footer className="mt-4 border-t border-rule bg-surface">
        <div className="mx-auto max-w-[1400px] px-4 py-5 sm:px-6">
          <p className="max-w-[80ch] text-sm text-muted">
            Every figure here is illustrative demo data, generated to exercise
            the platform. It is not verified fund performance and is not
            investment advice. The architecture is built to plug in licensed
            data once AIA has access.
          </p>
        </div>
      </footer>
    </div>
  );
}
