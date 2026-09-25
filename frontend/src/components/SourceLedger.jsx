import DataStatus from "./DataStatus";

/**
 * The audit trail behind the figures.
 *
 * Private-market data is incomplete by nature, so AltLens shows the gaps
 * rather than papering over them: what the source was, which field it
 * supports, and how much weight it carries.
 */
export default function SourceLedger({ sources, limit }) {
  if (!sources?.length) {
    return <p className="text-sm text-muted">No sources recorded.</p>;
  }

  const shown = limit ? sources.slice(0, limit) : sources;

  return (
    <div>
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-rule text-micro text-muted">
            <th scope="col" className="py-1.5 text-left font-medium">
              Source
            </th>
            <th scope="col" className="py-1.5 text-left font-medium">
              Field
            </th>
            <th scope="col" className="py-1.5 text-left font-medium">
              Confidence
            </th>
            <th scope="col" className="py-1.5 text-left font-medium">
              Note
            </th>
          </tr>
        </thead>
        <tbody>
          {shown.map((source, index) => (
            <tr
              key={`${source.source_name}-${source.field_name}-${index}`}
              className="border-b border-rule/60 align-top last:border-0"
            >
              <th scope="row" className="py-1.5 text-left font-normal">
                <span className="flex items-baseline gap-1.5">
                  <DataStatus status={source.data_status} />
                  {source.source_url ? (
                    <a
                      href={source.source_url}
                      className="text-accent underline underline-offset-2"
                      target="_blank"
                      rel="noreferrer"
                    >
                      {source.source_name}
                    </a>
                  ) : (
                    source.source_name
                  )}
                </span>
              </th>
              <td className="py-1.5">{source.field_name ?? "—"}</td>
              <td className="py-1.5 capitalize">{source.confidence}</td>
              <td className="max-w-[40ch] py-1.5 text-muted">{source.notes}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {limit && sources.length > limit ? (
        <p className="mt-2 text-micro text-muted">
          Showing {limit} of {sources.length} source records.
        </p>
      ) : null}
    </div>
  );
}
