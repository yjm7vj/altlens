import { useEffect, useState } from "react";

import { api } from "../api/client";
import { formatMultiple, formatPercent } from "../format";

const METRICS = [
  { key: "irr", label: "IRR" },
  { key: "moic", label: "MOIC" },
  { key: "dpi", label: "DPI" },
];

export default function TopPerformersWidget({ onSelect }) {
  const [metric, setMetric] = useState("irr");
  const [performers, setPerformers] = useState([]);

  useEffect(() => {
    let cancelled = false;

    api
      .topPerformers(metric, 5)
      .then((data) => {
        if (!cancelled) setPerformers(data);
      })
      .catch(() => {
        if (!cancelled) setPerformers([]);
      });

    return () => {
      cancelled = true;
    };
  }, [metric]);

  const leader = performers[0];
  const format = metric === "irr" ? formatPercent : formatMultiple;

  return (
    <section className="panel p-5" aria-labelledby="leaders-heading">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="leaders-heading" className="text-sm font-semibold">
          Leaders
        </h2>
        <div className="flex gap-1">
          {METRICS.map((entry) => (
            <button
              key={entry.key}
              type="button"
              onClick={() => setMetric(entry.key)}
              className={`border px-1.5 py-0.5 text-micro ${
                metric === entry.key
                  ? "border-ink text-ink"
                  : "border-rule text-muted hover:text-ink"
              }`}
              aria-pressed={metric === entry.key}
            >
              {entry.label}
            </button>
          ))}
        </div>
      </div>

      <ol className="mt-3 space-y-2">
        {performers.map((item, index) => (
          <li key={item.fund.id}>
            <button
              type="button"
              onClick={() => onSelect?.(item.fund.id)}
              className="flex w-full items-baseline gap-3 text-left hover:text-accent"
            >
              <span className="w-3 text-micro text-muted">{index + 1}</span>
              <span className="min-w-0 flex-1 truncate text-sm">
                {item.fund.name}
              </span>
              <span
                className={`figure tabular-nums ${
                  item === leader ? "text-base" : "text-sm"
                }`}
              >
                {format(item.metrics[metric])}
              </span>
            </button>
          </li>
        ))}
      </ol>
    </section>
  );
}
