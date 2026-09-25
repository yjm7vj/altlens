import { formatUsd } from "../format";

/**
 * Sector concentration as a single stacked band plus a ranked list.
 *
 * A pie chart would make the reader compare wedge angles; the thing an
 * analyst actually wants to know is how much of the portfolio sits in the top
 * one or two sectors, which a proportional band answers directly.
 */

const SHADES = [
  "#0F5C63",
  "#2F3E8F",
  "#A9762B",
  "#3C4658",
  "#6B8F93",
  "#8C2F29",
  "#96A3B8",
  "#C2A05A",
];

export default function SectorExposure({ exposures }) {
  if (!exposures?.length) {
    return <p className="text-sm text-muted">No portfolio companies recorded.</p>;
  }

  const top = exposures.slice(0, 8);

  return (
    <div>
      <div
        className="flex h-6 w-full overflow-hidden rounded-panel border border-rule"
        role="img"
        aria-label={`Sector concentration: ${top
          .map(
            (item) =>
              `${item.sector} ${(Number(item.share_of_value) * 100).toFixed(0)}%`,
          )
          .join(", ")}`}
      >
        {top.map((exposure, index) => (
          <div
            key={exposure.sector}
            style={{
              width: `${Number(exposure.share_of_value) * 100}%`,
              backgroundColor: SHADES[index % SHADES.length],
            }}
            title={`${exposure.sector}: ${(
              Number(exposure.share_of_value) * 100
            ).toFixed(1)}%`}
          />
        ))}
      </div>

      <ul className="mt-3 space-y-1.5">
        {top.map((exposure, index) => (
          <li
            key={exposure.sector}
            className="flex items-baseline gap-2 text-sm"
          >
            <span
              aria-hidden="true"
              className="mt-1 h-2 w-2 shrink-0 rounded-sm"
              style={{ backgroundColor: SHADES[index % SHADES.length] }}
            />
            <span className="flex-1 truncate">{exposure.sector}</span>
            <span className="figure tabular-nums">
              {(Number(exposure.share_of_value) * 100).toFixed(1)}%
            </span>
            <span className="w-16 text-right text-micro text-muted">
              {formatUsd(exposure.current_value_usd)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
