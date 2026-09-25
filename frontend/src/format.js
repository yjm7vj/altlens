export function formatPercent(value, digits = 1) {
  if (value === null || value === undefined) return "n/a";
  return `${(Number(value) * 100).toFixed(digits)}%`;
}

export function formatMultiple(value, digits = 2) {
  if (value === null || value === undefined) return "n/a";
  return `${Number(value).toFixed(digits)}x`;
}

export function formatUsd(value) {
  if (value === null || value === undefined) return "n/a";

  const amount = Number(value);
  const absolute = Math.abs(amount);
  const sign = amount < 0 ? "-" : "";

  if (absolute >= 1_000_000_000) {
    return `${sign}$${(absolute / 1_000_000_000).toFixed(2)}B`;
  }

  if (absolute >= 1_000_000) {
    return `${sign}$${Math.round(absolute / 1_000_000)}M`;
  }

  if (absolute >= 1_000) {
    return `${sign}$${Math.round(absolute / 1_000)}K`;
  }

  return `${sign}$${absolute.toFixed(0)}`;
}

export function formatDate(value) {
  if (!value) return "";
  const parsed = new Date(`${value}T00:00:00`);
  return parsed.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
  });
}

export function formatStage(stage) {
  if (!stage) return "";
  return stage
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
