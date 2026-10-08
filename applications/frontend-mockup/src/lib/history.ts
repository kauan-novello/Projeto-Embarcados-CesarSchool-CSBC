import {
  endOfDay,
  format,
  isWithinInterval,
  startOfDay,
  startOfMonth,
  startOfWeek,
} from "date-fns"
import { ptBR } from "date-fns/locale"
import { hashSeed, seededRandom } from "@/lib/prng"
import { getSeason, type Season } from "@/lib/seasons"
import type { PVSystem } from "@/types"

export interface Reading {
  timestamp: Date
  powerW: number
  predictedPowerW: number
  panelTempC: number
  ambientTempC: number
  ambientHumidityPct: number
  irradiance: number
}

export type GroupingLevel = "hour" | "day" | "week" | "month"

export interface GroupedRow {
  key: string
  label: string
  start: Date
  season: Season
  count: number
  powerW: number
  predictedPowerW: number
  panelTempC: number
  ambientTempC: number
  ambientHumidityPct: number
  irradiance: number
}

/** Gera leituras horárias determinísticas (mesmo systemId => mesmo histórico) cobrindo os últimos `daysBack` dias. */
export function generateHistoricalReadings(system: PVSystem, daysBack: number): Reading[] {
  const now = new Date()
  const totalHours = daysBack * 24
  const readings: Reading[] = []

  for (let h = totalHours; h >= 0; h--) {
    const timestamp = new Date(now.getTime() - h * 60 * 60 * 1000)
    const hourOfDay = timestamp.getHours()
    const daylightFactor = hourOfDay >= 6 && hourOfDay <= 18 ? Math.sin(((hourOfDay - 6) / 12) * Math.PI) : 0
    const noise = seededRandom(hashSeed(system.id, h))

    readings.push({
      timestamp,
      powerW: Math.round(daylightFactor * 1800 + noise * 80),
      // baseline que o modelo preveria para este horário/época, sem o ruído real (clima, sujeira no painel etc.)
      predictedPowerW: Math.round(daylightFactor * 1800),
      panelTempC: Math.round((28 + daylightFactor * 22 + noise * 4) * 10) / 10,
      ambientTempC: Math.round((24 + daylightFactor * 6 + noise * 3) * 10) / 10,
      ambientHumidityPct: Math.round(50 + noise * 25),
      irradiance: Math.round(daylightFactor * 95 + noise * 8),
    })
  }

  return readings
}

export function filterReadingsByRange(readings: Reading[], from: Date, to: Date): Reading[] {
  const interval = { start: startOfDay(from), end: endOfDay(to) }
  return readings.filter((r) => isWithinInterval(r.timestamp, interval))
}

function bucketFor(date: Date, grouping: GroupingLevel): { key: string; start: Date; label: string } {
  switch (grouping) {
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

  const avg = (items: Reading[], pick: (r: Reading) => number) =>
    items.reduce((sum, r) => sum + pick(r), 0) / items.length

  const rows: GroupedRow[] = Array.from(buckets.entries()).map(([key, { start, label, items }]) => ({
    key,
    label,
    start,
    season: getSeason(start),
    count: items.length,
    powerW: Math.round(avg(items, (r) => r.powerW)),
    predictedPowerW: Math.round(avg(items, (r) => r.predictedPowerW)),
    panelTempC: Math.round(avg(items, (r) => r.panelTempC) * 10) / 10,
    ambientTempC: Math.round(avg(items, (r) => r.ambientTempC) * 10) / 10,
    ambientHumidityPct: Math.round(avg(items, (r) => r.ambientHumidityPct)),
    irradiance: Math.round(avg(items, (r) => r.irradiance)),
  }))

  return rows.sort((a, b) => b.start.getTime() - a.start.getTime())
}
