/**
 * Provenance marker.
 *
 * Every figure in AltLens carries one of these, and the same glyph appears in
 * the source ledger. The glyph is the product's core claim made visible: you
 * can always see whether a number is verified, estimated, or made up for the
 * demo.
 */

const STATUS = {
  verified: {
    glyph: "■", // filled square
    label: "Verified",
    className: "text-realized",
    description: "Traced to a named source document.",
  },
  estimated: {
    glyph: "◧", // half-filled square
    label: "Estimated",
    className: "text-unrealized",
    description: "Derived or inferred, with the method recorded.",
  },
  illustrative: {
    glyph: "□", // hollow square
    label: "Illustrative",
    className: "text-muted",
    description: "Synthetic demo data. Not real fund performance.",
  },
};

export function statusOf(value) {
  return STATUS[value] ?? STATUS.illustrative;
}

export default function DataStatus({ status = "illustrative", showLabel = false }) {
  const entry = statusOf(status);

  return (
    <span
      className={`${entry.className} inline-flex items-center gap-1 text-micro`}
      title={`${entry.label}: ${entry.description}`}
    >
      <span aria-hidden="true">{entry.glyph}</span>
      {showLabel ? (
        <span>{entry.label}</span>
      ) : (
        <span className="sr-only">{entry.label} data</span>
      )}
    </span>
  );
}

export function DataStatusLegend() {
  return (
    <dl className="flex flex-wrap items-center gap-x-5 gap-y-1 text-micro text-muted">
      {Object.entries(STATUS).map(([key, entry]) => (
        <div key={key} className="flex items-center gap-1.5">
          <dt className={entry.className} aria-hidden="true">
            {entry.glyph}
          </dt>
          <dd>
            <span className="text-ink">{entry.label}</span> {entry.description}
          </dd>
        </div>
      ))}
    </dl>
  );
}
