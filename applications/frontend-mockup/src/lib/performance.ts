import { subDays } from "date-fns"
import type { Reading } from "@/lib/history"

export interface PerformanceStat {
  label: string
  actualKwh: number
  predictedKwh: number
  pct: number
}

/** Compara geração real x prevista (baseline sem ruído) nos últimos `days` dias. */
export function computePerformance(readings: Reading[], days: number, label: string): PerformanceStat {
  const cutoff = subDays(new Date(), days)
  const relevant = readings.filter((r) => r.timestamp >= cutoff)

  // leituras horárias: Wh acumulado ≈ soma de W (1h cada)
  const actualWh = relevant.reduce((sum, r) => sum + r.powerW, 0)
  const predictedWh = relevant.reduce((sum, r) => sum + r.predictedPowerW, 0)
  const pct = predictedWh > 0 ? Math.round((actualWh / predictedWh) * 100) : 100

  return {
    label,
    actualKwh: Math.round((actualWh / 1000) * 10) / 10,
    predictedKwh: Math.round((predictedWh / 1000) * 10) / 10,
    pct,
  }
}
