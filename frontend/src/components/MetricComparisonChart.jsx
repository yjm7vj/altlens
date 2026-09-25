import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

/**
 * Realized versus unrealized value, stacked.
 *
 * A 2.5x fund that has returned nothing in cash is a different proposition
 * from a 2.5x fund that has already paid it out, so the split is the chart
 * rather than a single MOIC bar.
 */
export default function MetricComparisonChart({ funds, height = 300 }) {
  if (!funds?.length) {
    return <p className="text-sm text-muted">No funds to compare.</p>;
  }

  const data = funds.map((item) => ({
    name: item.fund.name,
    dpi: Number(item.metrics.dpi ?? 0),
    rvpi: Number(item.metrics.rvpi ?? 0),
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 16, bottom: 4, left: 8 }}
        barCategoryGap={8}
      >
        <CartesianGrid stroke="#D3D8E0" horizontal={false} />
        <XAxis
          type="number"
          stroke="#5C6675"
          tick={{ fontSize: 11 }}
          tickFormatter={(value) => `${value}x`}
        />
        <YAxis
          type="category"
          dataKey="name"
          stroke="#5C6675"
          tick={{ fontSize: 11 }}
          width={150}
        />
        <Tooltip
          formatter={(value, name) => [`${Number(value).toFixed(2)}x`, name]}
          contentStyle={{
            border: "1px solid #D3D8E0",
            borderRadius: 3,
            fontSize: 12,
          }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="dpi" name="Returned in cash" stackId="value" fill="#0F5C63" />
        <Bar dataKey="rvpi" name="Held at NAV" stackId="value" fill="#A9762B" />
      </BarChart>
    </ResponsiveContainer>
  );
}
