import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatDate, formatUsd } from "../format";

/**
 * The J-curve.
 *
 * Capital goes out for years before anything comes back, and the moment
 * distributions overtake capital called is the single most meaningful date in
 * a fund's life. That crossover is marked explicitly rather than left for the
 * reader to find.
 */
export default function CapitalTimeline({ timeline, height = 320 }) {
  if (!timeline?.points?.length) {
    return (
      <p className="text-sm text-muted">
        No cash-flow history available for this selection.
      </p>
    );
  }

  const data = timeline.points.map((point) => ({
    date: point.period_date,
    called: Number(point.cumulative_called_usd),
    distributed: Number(point.cumulative_distributed_usd),
    nav: point.nav_usd === null ? null : Number(point.nav_usd),
  }));

  return (
    <figure className="m-0">
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
          <CartesianGrid stroke="#D3D8E0" vertical={false} />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            stroke="#5C6675"
            tick={{ fontSize: 11 }}
            minTickGap={28}
          />
          <YAxis
            tickFormatter={formatUsd}
            stroke="#5C6675"
            tick={{ fontSize: 11 }}
            width={58}
          />
          <Tooltip
            formatter={(value, name) => [formatUsd(value), name]}
            labelFormatter={formatDate}
            contentStyle={{
              border: "1px solid #D3D8E0",
              borderRadius: 3,
              fontSize: 12,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Area
            type="stepAfter"
            dataKey="nav"
            name="Held at NAV"
            stroke="#A9762B"
            fill="#EEDFC5"
            connectNulls
          />
          <Line
            type="stepAfter"
            dataKey="called"
            name="Capital called"
            stroke="#3C4658"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="stepAfter"
            dataKey="distributed"
            name="Capital returned"
            stroke="#0F5C63"
            strokeWidth={2}
            dot={false}
          />
          {timeline.break_even_date ? (
            <ReferenceLine
              x={timeline.break_even_date}
              stroke="#0F5C63"
              strokeDasharray="4 3"
              label={{
                value: "Break-even",
                position: "insideTopLeft",
                fill: "#0F5C63",
                fontSize: 11,
              }}
            />
          ) : null}
        </ComposedChart>
      </ResponsiveContainer>
      <figcaption className="mt-2 text-micro text-muted">
        {timeline.break_even_date
          ? `Distributions overtook capital called in ${formatDate(
              timeline.break_even_date,
            )}.`
          : "Distributions have not yet overtaken capital called."}
      </figcaption>
    </figure>
  );
}
