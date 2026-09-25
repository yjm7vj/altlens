const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;

    try {
      const body = await response.json();
      if (body?.detail) {
        detail = typeof body.detail === "string" ? body.detail : detail;
      }
    } catch {
      // Response had no JSON body; the status-code message stands.
    }

    throw new Error(detail);
  }

  return response.json();
}

export const api = {
  health: () => request("/api/health"),
  funds: () => request("/api/funds"),
  fundsWithMetrics: () => request("/api/funds/with-metrics"),
  fund: (fundId) => request(`/api/funds/${fundId}`),
  fundPerformance: (fundId) => request(`/api/funds/${fundId}/performance`),
  topPerformers: (metric = "moic", limit = 5) =>
    request(`/api/metrics/top?metric=${metric}&limit=${limit}`),
  vintages: () => request("/api/metrics/vintages"),
  sectors: () => request("/api/metrics/sectors"),
  sources: () => request("/api/sources"),
  methodology: (metric) => request(`/api/metrics/methodology/${metric}`),
  aiTools: () => request("/api/ai/tools"),
  aiProviders: () => request("/api/ai/providers"),
  askAI: (question, provider) =>
    request("/api/ai/query", {
      method: "POST",
      body: JSON.stringify({ question, provider: provider ?? null }),
    }),
};
