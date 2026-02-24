export function formatDate(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export function formatPrediction(prediction?: number[] | Record<string, unknown> | null) {
  if (!prediction) return "-";
  if (Array.isArray(prediction)) {
    return prediction.slice(0, 5).map((x) => x.toFixed(3)).join(", ");
  }
  return JSON.stringify(prediction);
}
