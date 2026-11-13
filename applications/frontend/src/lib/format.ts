export function formatMetric(value: number | null, unit: string): string {
  return value === null ? "—" : `${Math.round(value * 10) / 10}${unit}`
}
