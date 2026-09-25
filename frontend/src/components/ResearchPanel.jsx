import { useEffect, useState } from "react";

import ResearchBriefView from "./ResearchBriefView";
import { api } from "../api/client";

const EXAMPLES = [
  "Which fund had the best performance?",
  "Compare AltLens Ventures I and Summit Growth VC III",
  "What is the average MOIC across all funds?",
  "Create a research brief on 2018 vintage funds",
  "How is IRR calculated?",
];

/**
 * Ask a question, see which approved tools ran, then read the answer.
 *
 * The tool trace sits above the answer on purpose: the point of AltLens is
 * that you can see exactly which calculation produced a figure before you
 * read the sentence built on top of it.
 */
export default function ResearchPanel() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [providers, setProviders] = useState([]);
  const [provider, setProvider] = useState("");

  useEffect(() => {
    api
      .aiProviders()
      .then(setProviders)
      .catch(() => setProviders([]));
  }, []);

  async function ask(asked) {
    const text = (asked ?? question).trim();
    if (!text) return;

    setQuestion(text);
    setLoading(true);
    setError(null);

    try {
      setResult(await api.askAI(text, provider || null));
    } catch (problem) {
      setError(problem.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel p-5" aria-labelledby="research-heading">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="research-heading" className="text-sm font-semibold">
          Ask the data
        </h2>
        {providers.length ? (
          <label className="flex items-center gap-2 text-micro text-muted">
            Model
            <select
              value={provider}
              onChange={(event) => setProvider(event.target.value)}
              className="border border-rule bg-surface px-1.5 py-0.5 text-micro text-ink"
            >
              <option value="">Default</option>
              {providers.map((entry) => (
                <option
                  key={entry.name}
                  value={entry.name}
                  disabled={!entry.available}
                >
                  {entry.name}
                  {entry.available ? "" : " (not configured)"}
                </option>
              ))}
            </select>
          </label>
        ) : null}
      </div>

      <form
        className="mt-3 flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          ask();
        }}
      >
        <label htmlFor="research-question" className="sr-only">
          Research question
        </label>
        <input
          id="research-question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Which 2019 funds have the weakest DPI?"
          className="min-w-0 flex-1 border border-rule bg-surface px-3 py-2 text-sm placeholder:text-muted"
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="bg-ink px-4 py-2 text-sm text-canvas disabled:opacity-40"
        >
          {loading ? "Working" : "Ask"}
        </button>
      </form>

      <ul className="mt-2.5 flex flex-wrap gap-1.5">
        {EXAMPLES.map((example) => (
          <li key={example}>
            <button
              type="button"
              onClick={() => ask(example)}
              className="border border-rule px-2 py-1 text-micro text-muted hover:border-accent hover:text-accent"
            >
              {example}
            </button>
          </li>
        ))}
      </ul>

      {error ? (
        <p className="mt-4 border-l-2 border-negative pl-3 text-sm text-negative">
          {error}
        </p>
      ) : null}

      {result ? (
        <div className="mt-4">
          {result.tool_calls?.length ? (
            <div className="border-b border-rule pb-3">
              <h3 className="text-micro text-muted">
                Tools run to answer this
              </h3>
              <ul className="mt-1 space-y-0.5 text-micro">
                {result.tool_calls.map((call, index) => (
                  <li key={`${call.tool_name}-${index}`}>
                    <code className="text-accent">{call.tool_name}</code>
                    <span className="text-muted">
                      {Object.keys(call.arguments ?? {}).length
                        ? ` (${JSON.stringify(call.arguments)})`
                        : " ()"}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="border-b border-rule pb-3 text-micro text-muted">
              No tool could answer this, so no figures were produced.
            </p>
          )}

          <p className="mt-3 whitespace-pre-wrap font-serif text-[0.95rem] leading-relaxed">
            {result.answer}
          </p>

          <p className="mt-2 text-micro text-muted">
            Answered by {result.provider}
            {result.model ? ` (${result.model})` : ""}.
          </p>

          <ResearchBriefView brief={result.brief} onFollowUp={ask} />
        </div>
      ) : null}
    </section>
  );
}
