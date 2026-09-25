import { useEffect, useState } from "react";

import CapitalTimeline from "./CapitalTimeline";
import DataStatus from "./DataStatus";
import SourceLedger from "./SourceLedger";
import { api } from "../api/client";
import {
  formatDate,
  formatMultiple,
  formatPercent,
  formatStage,
  formatUsd,
} from "../format";

function Figure({ label, value, tone }) {
  const toneClass =
    tone === "realized"
      ? "text-realized"
      : tone === "unrealized"
        ? "text-unrealized"
        : "text-ink";

  return (
    <div className="min-w-0">
      <dt className="field-label">{label}</dt>
      <dd className={`figure text-lg tabular-nums ${toneClass}`}>{value}</dd>
    </div>
  );
}

export default function FundDetail({ fundId, onClose }) {
  const [detail, setDetail] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setDetail(null);
    setTimeline(null);
    setError(null);

    api
      .fund(fundId)
      .then((data) => {
        if (cancelled) return;
        setDetail(data);
        return fetch(
          `/api/metrics/capital-timeline?fund_names=${encodeURIComponent(
            data.fund.name,
          )}`,
        ).then((response) => response.json());
      })
      .then((data) => {
        if (!cancelled && data) setTimeline(data);
      })
      .catch((problem) => {
        if (!cancelled) setError(problem.message);
      });

    return () => {
      cancelled = true;
    };
  }, [fundId]);

  if (error) {
    return (
      <section className="panel p-5">
        <p className="text-sm text-negative">{error}</p>
      </section>
    );
  }

  if (!detail) {
    return (
      <section className="panel p-5">
        <p className="text-sm text-muted">Loading fund…</p>
      </section>
    );
  }

  const { fund, metrics, positions, cash_flows: cashFlows, sources } = detail;

  return (
    <section className="panel p-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-xl font-semibold tracking-tight">{fund.name}</h2>
          <p className="mt-1 text-sm text-muted">
            {fund.manager_name}, {fund.vintage_year} vintage. {fund.strategy}.{" "}
            {fund.geography}.
          </p>
          {fund.description ? (
            <p className="mt-2 max-w-[62ch] font-serif text-[0.95rem] leading-relaxed">
              {fund.description}
            </p>
          ) : null}
        </div>
        <div className="flex items-center gap-3">
          <DataStatus status={fund.data_quality} showLabel />
          {onClose ? (
            <button
              type="button"
              onClick={onClose}
              className="border border-rule px-2 py-1 text-micro text-muted hover:text-ink"
            >
              Close
            </button>
          ) : null}
        </div>
      </header>

      <dl className="mt-5 grid grid-cols-2 gap-x-6 gap-y-4 border-y border-rule py-4 sm:grid-cols-3 lg:grid-cols-6">
        <Figure label="IRR" value={formatPercent(metrics.irr)} />
        <Figure label="MOIC" value={formatMultiple(metrics.moic)} />
        <Figure
          label="DPI, returned in cash"
          value={formatMultiple(metrics.dpi)}
          tone="realized"
        />
        <Figure
          label="RVPI, held at NAV"
          value={formatMultiple(metrics.rvpi)}
          tone="unrealized"
        />
        <Figure label="Paid in" value={formatUsd(metrics.paid_in_usd)} />
        <Figure label="Distributed" value={formatUsd(metrics.distributed_usd)} />
      </dl>

      {timeline ? (
        <div className="mt-5">
          <h3 className="text-sm font-semibold">Capital called and returned</h3>
          <div className="mt-2">
            <CapitalTimeline timeline={timeline} height={260} />
          </div>
        </div>
      ) : null}

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div>
          <h3 className="text-sm font-semibold">Portfolio companies</h3>
          {positions.length ? (
            <table className="mt-2 w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-rule text-micro text-muted">
                  <th scope="col" className="py-1.5 text-left font-medium">
                    Company
                  </th>
                  <th scope="col" className="py-1.5 text-left font-medium">
                    Sector
                  </th>
                  <th scope="col" className="py-1.5 text-right font-medium">
                    Invested
                  </th>
                  <th scope="col" className="py-1.5 text-right font-medium">
                    Marked at
                  </th>
                </tr>
              </thead>
              <tbody>
                {positions.map((position) => (
                  <tr
                    key={position.company_name}
                    className="border-b border-rule/60 last:border-0"
                  >
                    <th scope="row" className="py-1.5 text-left font-normal">
                      {position.company_name}
                      <span className="block text-micro text-muted">
                        {formatStage(position.stage)}
                        {position.status !== "active"
                          ? `, ${position.status.replace("_", " ")}`
                          : ""}
                      </span>
                    </th>
                    <td className="py-1.5">{position.sector}</td>
                    <td className="py-1.5 text-right tabular-nums">
                      {formatUsd(position.invested_usd)}
                    </td>
                    <td
                      className={`py-1.5 text-right tabular-nums ${
                        Number(position.current_value_usd) <
                        Number(position.invested_usd)
                          ? "text-negative"
                          : ""
                      }`}
                    >
                      {formatUsd(position.current_value_usd)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="mt-2 text-sm text-muted">
              No portfolio companies recorded for this fund.
            </p>
          )}
        </div>

        <div>
          <h3 className="text-sm font-semibold">Cash-flow events</h3>
          <table className="mt-2 w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-rule text-micro text-muted">
                <th scope="col" className="py-1.5 text-left font-medium">
                  Date
                </th>
                <th scope="col" className="py-1.5 text-left font-medium">
                  Event
                </th>
                <th scope="col" className="py-1.5 text-right font-medium">
                  Amount
                </th>
              </tr>
            </thead>
            <tbody>
              {cashFlows.map((flow) => (
                <tr
                  key={`${flow.event_date}-${flow.amount_usd}`}
                  className="border-b border-rule/60 last:border-0"
                >
                  <td className="py-1.5">{formatDate(flow.event_date)}</td>
                  <td className="py-1.5">
                    {flow.flow_type === "capital_call"
                      ? "Capital call"
                      : "Distribution"}
                  </td>
                  <td
                    className={`py-1.5 text-right tabular-nums ${
                      flow.flow_type === "capital_call"
                        ? "text-called"
                        : "text-realized"
                    }`}
                  >
                    {formatUsd(flow.amount_usd)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-6">
        <h3 className="text-sm font-semibold">Where this data came from</h3>
        <div className="mt-2">
          <SourceLedger sources={sources} />
        </div>
      </div>
    </section>
  );
}
