import { addDays, endOfDay, isSameDay, startOfHour, subDays } from "date-fns"
import { apiFetch } from "./api"
import type { HourComparison } from "@/types"

interface HourComparisonResponse {
  hour_start: string
  kind: string
  predicted_energy_wh: number
  real_energy_wh: number | null
  model_version: string
}

const MIN_EXPECTED_FOR_PERFORMANCE_WH = 2000

export const MIN_SUN_HOUR_WH = 200

export type PredictionKind = "observed" | "forecast"

export async function listHourComparisons(
  systemId: string,
  from: Date,
  to: Date,
  kind: PredictionKind = "observed",
): Promise<HourComparison[]> {
  const params = new URLSearchParams({ from: from.toISOString(), to: to.toISOString(), kind })
  const response = await apiFetch<HourComparisonResponse[]>(`/systems/${systemId}/predictions?${params}`)
  return response.map((row) => ({
    hourStart: new Date(row.hour_start),
    expectedWh: row.predicted_energy_wh,
    realWh: row.real_energy_wh,
    modelVersion: row.model_version,
  }))
}

export function listRecentComparisons(systemId: string, now: Date, days = 7): Promise<HourComparison[]> {
  return listHourComparisons(systemId, subDays(now, days), now)
}

export function lastComparedHour(hours: HourComparison[]): HourComparison | null {
  for (let i = hours.length - 1; i >= 0; i--) {
    if (performancePct(hours[i].expectedWh, hours[i].realWh) !== null) return hours[i]
  }
  return null
}

export function performancePct(expectedWh: number, realWh: number | null): number | null {
  if (realWh === null || expectedWh < MIN_EXPECTED_FOR_PERFORMANCE_WH) return null
  return Math.round((realWh / expectedWh) * 100)
}

export function comparedTotals(hours: HourComparison[]): { expectedWh: number; realWh: number } {
  return hours.reduce(
    (acc, h) => (h.realWh === null ? acc : { expectedWh: acc.expectedWh + h.expectedWh, realWh: acc.realWh + h.realWh }),
    { expectedWh: 0, realWh: 0 },
  )
}

export function listForecast(systemId: string, now: Date): Promise<HourComparison[]> {
  return listHourComparisons(systemId, startOfHour(now), endOfDay(addDays(now, 1)), "forecast")
}

export function totalForDay(hours: HourComparison[], day: Date): number {
  return hours.filter((h) => isSameDay(h.hourStart, day)).reduce((sum, h) => sum + h.expectedWh, 0)
}
