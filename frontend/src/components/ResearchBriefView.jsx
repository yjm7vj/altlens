import SourceLedger from "./SourceLedger";

/**
 * A generated brief, rendered as a document rather than a chat bubble.
 *
 * The order is deliberate: what we found, the numbers behind it, then every
 * reason to doubt it. Assumptions and data-quality notes are never collapsed
 * away.
 */
export default function ResearchBriefView({ brief, onFollowUp }) {
  if (!brief) return null;

  return (
    <article className="mt-4 border-t border-rule pt-4">
      <h3 className="text-sm font-semibold">Research brief</h3>
      <p className="mt-2 max-w-[68ch] font-serif text-[0.95rem] leading-relaxed">
        {brief.summary}
      </p>

      {brief.sections?.length ? (
        <div className="mt-4 space-y-3">
          {brief.sections.map((section) => (
            <section key={section.title}>
              <h4 className="text-micro text-muted">{section.title}</h4>
              <p className="mt-0.5 max-w-[68ch] font-serif text-[0.95rem] leading-relaxed">
                {section.body}
              </p>
            </section>
          ))}
        </div>
      ) : null}

      {brief.tables?.map((table) => (
        <div key={table.title} className="mt-4 overflow-x-auto">
          <h4 className="text-micro text-muted">{table.title}</h4>
          <table className="mt-1 w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-rule text-micro text-muted">
                {table.columns.map((column, index) => (
                  <th
                    key={column}
                    scope="col"
                    className={`py-1.5 font-medium ${
                      index === 0 ? "text-left" : "text-right"
                    }`}
                  >
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((row) => (
                <tr key={row[0]} className="border-b border-rule/60 last:border-0">
                  {row.map((cell, index) => (
                    <td
                      key={`${row[0]}-${index}`}
                      className={`py-1.5 tabular-nums ${
                        index === 0 ? "text-left" : "text-right"
                      }`}
                    >
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}

      {brief.assumptions?.length ? (
        <section className="mt-4">
          <h4 className="text-micro text-muted">Assumptions</h4>
          <ul className="mt-1 max-w-[68ch] list-disc space-y-0.5 pl-5 text-sm">
            {brief.assumptions.map((assumption) => (
              <li key={assumption}>{assumption}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {brief.data_quality_notes?.length ? (
        <section className="mt-4 border-l-2 border-unrealized pl-3">
          <h4 className="text-micro text-muted">Reasons to doubt this</h4>
          <ul className="mt-1 max-w-[68ch] space-y-0.5 text-sm">
            {brief.data_quality_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {brief.sources?.length ? (
        <section className="mt-4">
          <h4 className="text-micro text-muted">Sources</h4>
          <div className="mt-1">
            <SourceLedger sources={brief.sources} limit={6} />
          </div>
        </section>
      ) : null}

      {brief.follow_up_questions?.length ? (
        <section className="mt-4">
          <h4 className="text-micro text-muted">Ask next</h4>
          <ul className="mt-1.5 flex flex-wrap gap-2">
            {brief.follow_up_questions.map((question) => (
              <li key={question}>
                <button
                  type="button"
                  onClick={() => onFollowUp?.(question)}
                  className="border border-rule px-2 py-1 text-left text-micro hover:border-accent hover:text-accent"
                >
                  {question}
                </button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </article>
  );
}
