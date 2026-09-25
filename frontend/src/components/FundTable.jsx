import { useMemo, useState } from "react";

import DataStatus from "./DataStatus";
import { formatMultiple, formatPercent, formatUsd } from "../format";

const COLUMNS = [
  { key: "name", label: "Fund", numeric: false },
  { key: "vintage_year", label: "Vintage", numeric: true },
  { key: "fund_size_usd", label: "Size", numeric: true },
  { key: "irr", label: "IRR", numeric: true },
  { key: "moic", label: "MOIC", numeric: true },
  { key: "dpi", label: "DPI", numeric: true },
  { key: "rvpi", label: "RVPI", numeric: true },
];

function valueFor(row, key) {
  if (key === "name") return row.fund.name;
  if (key === "vintage_year") return row.fund.vintage_year ?? 0;
  if (key === "fund_size_usd") return Number(row.fund.fund_size_usd ?? 0);
  return Number(row.metrics[key] ?? 0);
}

export default function FundTable({ rows, selectedFundId, onSelect }) {
  const [sortKey, setSortKey] = useState("moic");
  const [descending, setDescending] = useState(true);

  const sorted = useMemo(() => {
    const copy = [...(rows ?? [])];

    copy.sort((left, right) => {
      const a = valueFor(left, sortKey);
      const b = valueFor(right, sortKey);

      if (typeof a === "string") {
        return descending ? b.localeCompare(a) : a.localeCompare(b);
      }

      return descending ? b - a : a - b;
    });

    return copy;
  }, [rows, sortKey, descending]);

  function toggleSort(key) {
    if (key === sortKey) {
      setDescending((current) => !current);
      return;
    }

    setSortKey(key);
    setDescending(true);
  }

  if (!rows?.length) {
    return <p className="text-sm text-muted">No funds match the current filters.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-rule text-micro text-muted">
            {COLUMNS.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={`py-2 font-medium ${
                  column.numeric ? "text-right" : "text-left"
                }`}
              >
                <button
                  type="button"
                  onClick={() => toggleSort(column.key)}
                  className="hover:text-ink"
                  aria-sort={
                    sortKey === column.key
                      ? descending
                        ? "descending"
                        : "ascending"
                      : "none"
                  }
                >
                  {column.label}
                  {sortKey === column.key ? (
                    <span aria-hidden="true">{descending ? " ↓" : " ↑"}</span>
                  ) : null}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => {
            const selected = row.fund.id === selectedFundId;

            return (
              <tr
                key={row.fund.id}
                className={`border-b border-rule/60 last:border-0 ${
                  selected ? "bg-realizedSoft/40" : "hover:bg-canvas"
                }`}
              >
                <th scope="row" className="py-2 text-left font-normal">
                  <button
                    type="button"
                    onClick={() => onSelect?.(row.fund.id)}
                    className="flex items-baseline gap-2 text-left hover:text-accent"
                  >
                    <DataStatus status={row.fund.data_quality} />
                    <span>
                      <span className="block">{row.fund.name}</span>
                      <span className="block text-micro text-muted">
                        {row.fund.manager_name}
                      </span>
                    </span>
                  </button>
                </th>
                <td className="py-2 text-right tabular-nums">
                  {row.fund.vintage_year}
                </td>
                <td className="py-2 text-right tabular-nums">
                  {formatUsd(row.fund.fund_size_usd)}
                </td>
                <td className="figure py-2 text-right tabular-nums">
                  {formatPercent(row.metrics.irr)}
                </td>
                <td className="figure py-2 text-right tabular-nums">
                  {formatMultiple(row.metrics.moic)}
                </td>
                <td className="py-2 text-right tabular-nums text-realized">
                  {formatMultiple(row.metrics.dpi)}
                </td>
                <td className="py-2 text-right tabular-nums text-unrealized">
                  {formatMultiple(row.metrics.rvpi)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
