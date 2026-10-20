import { format, startOfDay, startOfMinute, startOfMonth, startOfWeek } from "date-fns"
import { ptBR } from "date-fns/locale"
import { getSeason, type Season } from "@/lib/seasons"
import type { LiveMetrics } from "@/types"

export interface Reading {
  timestamp: Date
  powerW: number | null
  panelTempC: number | null
  ambientTempC: number | null
  ambientHumidityPct: number | null
  irradiance: number
  pressureHpa: number | null
  particulatePct: number | null
}

export type GroupingLevel = "reading" | "minute" | "hour" | "day" | "week" | "month"

export interface GroupedRow {
  key: string
  label: string
  start: Date
  season: Season
  count: number
  powerW: number | null
  panelTempC: number | null
  ambientTempC: number | null
  ambientHumidityPct: number | null
  irradiance: number
  pressureHpa: number | null
  particulatePct: number | null
}

export function toReading(metrics: LiveMetrics): Reading {
  return {
    timestamp: new Date(metrics.recordedAt),
    powerW: metrics.powerW,
    panelTempC: metrics.panelTempC,
    ambientTempC: metrics.ambientTempC,
    ambientHumidityPct: metrics.ambientHumidityPct,
    irradiance: metrics.irradiance,
    pressureHpa: metrics.pressureHpa,
    particulatePct: metrics.particulatePct,
  }
}

export function bucketFor(date: Date, grouping: GroupingLevel): { key: string; start: Date; label: string } {
  switch (grouping) {
    case "reading":
      return { key: date.toISOString(), start: date, label: format(date, "dd/MM/yyyy HH:mm:ss") }
    case "minute": {
      const start = startOfMinute(date)
      return { key: start.toISOString(), start, label: format(start, "dd/MM/yyyy HH:mm") }
    }
    case "hour": {
      const start = new Date(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours())
      return { key: start.toISOString(), start, label: format(start, "dd/MM/yyyy HH:00") }
    }
    case "day": {
      const start = startOfDay(date)
      return { key: start.toISOString(), start, label: format(start, "dd/MM/yyyy") }
    }
    case "week": {
      const start = startOfWeek(date, { weekStartsOn: 1 })
      return { key: start.toISOString(), start, label: `Semana de ${format(start, "dd/MM/yyyy")}` }
    }
    case "month": {
      const start = startOfMonth(date)
      const raw = format(start, "MMMM 'de' yyyy", { locale: ptBR })
      return { key: start.toISOString(), start, label: raw.charAt(0).toUpperCase() + raw.slice(1) }
    }
  }
}

export function groupReadings(readings: Reading[], grouping: GroupingLevel): GroupedRow[] {
  const buckets = new Map<string, { start: Date; label: string; items: Reading[] }>()

  for (const reading of readings) {
    const { key, start, label } = bucketFor(reading.timestamp, grouping)
    const bucket = buckets.get(key)
    if (bucket) {
      bucket.items.push(reading)
    } else {
      buckets.set(key, { start, label, items: [reading] })
    }
  }

  const avg = (items: Reading[], pick: (r: Reading) => number | null): number | null => {
    const values = items.map(pick).filter((v): v is number => v !== null)
    return values.length === 0 ? null : values.reduce((sum, v) => sum + v, 0) / values.length
  }
  const round = (value: number | null, decimals = 0): number | null => {
    if (value === null) return null
    const factor = 10 ** decimals
    return Math.round(value * factor) / factor
  }

  const rows: GroupedRow[] = Array.from(buckets.entries()).map(([key, { start, label, items }]) => ({
    key,
    label,
    start,
    season: getSeason(start),
    count: items.length,
    powerW: round(avg(items, (r) => r.powerW)),
    panelTempC: round(avg(items, (r) => r.panelTempC), 1),
    ambientTempC: round(avg(items, (r) => r.ambientTempC), 1),
    ambientHumidityPct: round(avg(items, (r) => r.ambientHumidityPct)),
    irradiance: round(avg(items, (r) => r.irradiance)) ?? 0,
    pressureHpa: round(avg(items, (r) => r.pressureHpa), 1),
    particulatePct: round(avg(items, (r) => r.particulatePct), 1),
  }))

  return rows.sort((a, b) => b.start.getTime() - a.start.getTime())
}
