import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

/** Median IRR and MOIC by vintage year, the standard private-market cohort view. */
export default function VintageChart({ vintages, height = 240 }) {
  if (!vintages?.length) {
    return <p className="text-sm text-muted">No vintage cohorts available.</p>;
  }

  const data = vintages.map((vintage) => ({
    year: String(vintage.vintage_year),
    irr: Number(vintage.median_irr ?? 0) * 100,
    moic: Number(vintage.median_moic ?? 0),
    funds: vintage.fund_count,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="#D3D8E0" vertical={false} />
        <XAxis dataKey="year" stroke="#5C6675" tick={{ fontSize: 11 }} />
        <YAxis
          yAxisId="left"
          stroke="#5C6675"
          tick={{ fontSize: 11 }}
          tickFormatter={(value) => `${value.toFixed(0)}%`}
          width={44}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          stroke="#5C6675"
          tick={{ fontSize: 11 }}
          tickFormatter={(value) => `${value.toFixed(1)}x`}
          width={44}
        />
        <Tooltip
          formatter={(value, name) =>
            name === "Median IRR"
              ? [`${Number(value).toFixed(1)}%`, name]
              : [`${Number(value).toFixed(2)}x`, name]
          }
          labelFormatter={(label) => `${label} vintage`}
          contentStyle={{
            border: "1px solid #D3D8E0",
            borderRadius: 3,
            fontSize: 12,
          }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar yAxisId="left" dataKey="irr" name="Median IRR" fill="#CFE2E3" />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="moic"
          name="Median MOIC"
          stroke="#A9762B"
          strokeWidth={2}
          dot={{ r: 3 }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
